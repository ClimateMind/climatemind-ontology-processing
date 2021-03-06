import pickle
import argparse
import networkx as nx
import pandas as pd
import validators

import owlready2
from owlready2 import sync_reasoner
from collections import OrderedDict

try:
    from graph_creation.ontology_processing_utils import (
        give_alias,
        save_test_ontology_to_json,
        save_graph_to_pickle,
        get_valid_test_ont,
        get_non_test_ont,
        remove_non_test_nodes,
        get_test_ontology,
    )
except ImportError:
    from ontology_processing.graph_creation.ontology_processing_utils import (
        give_alias,
        save_test_ontology_to_json,
        save_graph_to_pickle,
        get_valid_test_ont,
        get_non_test_ont,
        remove_non_test_nodes,
        get_test_ontology,
    )

# Set a lower JVM memory limit
owlready2.reasoning.JAVA_MEMORY = 500

# convenient source types list
SOURCE_TYPES = [
    "dc_source",
    "schema_academicBook",
    "schema_academicSourceNoPaywall",
    "schema_academicSourceWithPaywall",
    "schema_governmentSource",
    "schema_mediaSource",
    "schema_mediaSourceForConservatives",
    "schema_organizationSource",
]


def solution_sources(node, source_types):
    """Returns a flattened list of custom solution source values from each node key that matches
    custom_source_types string.
    node - NetworkX node
    source_types - list of sources types
    """
    # loop over each solution source key and append each returned value to the solution_sources list
    solution_source_list = list()
    for source_type in source_types:
        if "properties" in node and source_type in node["properties"]:
            solution_source_list.extend(node["properties"][source_type])

    solution_source_list = list(OrderedDict.fromkeys(solution_source_list))

    return solution_source_list


def listify(collection, onto):
    """just capturing a repeated operation"""
    return [str(thing.label[0]) for thing in collection if thing in onto.classes()]


def compute(values):
    """Collapse a vector potentially consisting of 0, 1, -1 and None to a single value.
    If a 1 or -1 is found they should always default to those values
    There should not be opposing values in the same vector or the ontology may
    need to be checked.
    """
    if all(v is None for v in values):
        final = None
    else:
        final = 0
        one_found = False
        neg_one_found = False

        for v in values:
            if v == 1:
                final = 1
                one_found = True
            if v == -1:
                final = -1
                neg_one_found = True
        if one_found and neg_one_found:
            raise Exception("Node found that has opposing vector values 1 and -1")

    return final


def add_ontology_data_to_graph_nodes(G, onto):
    """Find the equivalent nodes in the ontology and load in relevant data
    including the classes they belong to.

    Parameters
    ----------
    G: A networkx Graph
    onto: owlready2 ontology object
    """
    # This shouldn't need to be repeated for each node.
    # Moved out of loop.
    cm_class = onto.search_one(label="climate mind")
    superclasses = list(cm_class.subclasses())

    # get annotation properties for all objects of the ontology (whether node or class)
    annot_properties = [
        thing.label[0].replace(":", "_")
        for thing in list(onto.annotation_properties())
        if thing.label
    ]

    # get data properties for all objects of the ontology (whether node or class)
    data_properties = [
        thing.label[0].replace(" ", "_")
        for thing in list(onto.data_properties())
        if thing.label
    ]

    for node in list(G.nodes):
        ontology_node = onto.search_one(label=node)

        class_objects = onto.get_parents_of(ontology_node)

        attributes_dict = {}
        attributes_dict["label"] = str(ontology_node.label[0])
        attributes_dict["iri"] = str(ontology_node)
        attributes_dict["comment"] = str(ontology_node.comment)
        attributes_dict["direct classes"] = listify(class_objects, onto)

        all_classes = []
        for parent in class_objects:
            if parent in onto.classes():
                all_classes.extend(parent.ancestors())

        list_classes = listify(all_classes, onto)
        list_classes = list(set(list_classes))
        if "climate mind" in list_classes:
            list_classes.remove("climate mind")
        attributes_dict["all classes"] = list_classes

        # for each class in the classes associated with the node, list that class in the appropriate super_class in the attributes_dict and all of the ancestor classes of that class
        for node_class in class_objects:
            for super_class in superclasses:
                if node_class in super_class.descendants():
                    to_add = listify(node_class.ancestors(), onto)
                    if "climate mind" in to_add:
                        to_add.remove("climate mind")
                    if super_class in attributes_dict.keys():
                        attributes_dict[str(super_class.label[0])] = list(
                            set(attributes_dict[super_class]) | set(to_add)
                        )
                    else:
                        attributes_dict[str(super_class.label[0])] = to_add

        attributes_dict["properties"] = {
            prop: list(getattr(ontology_node, prop)) for prop in annot_properties
        }

        attributes_dict["data_properties"] = {
            prop: getattr(ontology_node, prop) for prop in data_properties
        }

        # format personal_values_10 and personal_values_19 to facilitate easier scoring later by the climate mind app
        # these are hard coded in and the order is very important. Later can change so these aren't hard coded and the order is always alphebetical(?)
        # use the compute function to collapse a value with multiple subvalues into one number. As long as there's any 1, then the final value is 1 (otherwise 0). None if all are None.

        personal_values_19 = [
            attributes_dict["data_properties"]["achievement"],
            attributes_dict["data_properties"]["benevolence_caring"],
            attributes_dict["data_properties"]["benevolence_dependability"],
            attributes_dict["data_properties"]["conformity_interpersonal"],
            attributes_dict["data_properties"]["conformity_rules"],
            attributes_dict["data_properties"]["face"],
            attributes_dict["data_properties"]["hedonism"],
            attributes_dict["data_properties"]["humility"],
            attributes_dict["data_properties"]["power_dominance"],
            attributes_dict["data_properties"]["power_resources"],
            attributes_dict["data_properties"]["security_personal"],
            attributes_dict["data_properties"]["security_societal"],
            attributes_dict["data_properties"]["self-direction_autonomy_of_action"],
            attributes_dict["data_properties"]["self-direction_autonomy_of_thought"],
            attributes_dict["data_properties"]["stimulation"],
            attributes_dict["data_properties"]["tradition"],
            attributes_dict["data_properties"]["universalism_concern"],
            attributes_dict["data_properties"]["universalism_nature"],
            attributes_dict["data_properties"]["universalism_tolerance"],
        ]

        achievement = attributes_dict["data_properties"]["achievement"]
        benevolence = compute(
            [
                attributes_dict["data_properties"]["benevolence_caring"],
                attributes_dict["data_properties"]["benevolence_dependability"],
            ]
        )
        conformity = compute(
            [
                attributes_dict["data_properties"]["conformity_interpersonal"],
                attributes_dict["data_properties"]["conformity_rules"],
            ]
        )
        hedonism = attributes_dict["data_properties"]["hedonism"]
        power = compute(
            [
                attributes_dict["data_properties"]["power_dominance"],
                attributes_dict["data_properties"]["power_resources"],
            ]
        )
        security = compute(
            [
                attributes_dict["data_properties"]["security_personal"],
                attributes_dict["data_properties"]["security_societal"],
            ]
        )
        self_direction = compute(
            [
                attributes_dict["data_properties"]["self-direction_autonomy_of_action"],
                attributes_dict["data_properties"][
                    "self-direction_autonomy_of_thought"
                ],
            ]
        )
        stimulation = attributes_dict["data_properties"]["stimulation"]
        tradition = attributes_dict["data_properties"]["tradition"]
        universalism = compute(
            [
                attributes_dict["data_properties"]["universalism_concern"],
                attributes_dict["data_properties"]["universalism_nature"],
                attributes_dict["data_properties"]["universalism_tolerance"],
            ]
        )

        personal_values_10 = [
            achievement,
            benevolence,
            conformity,
            hedonism,
            power,
            security,
            self_direction,
            stimulation,
            tradition,
            universalism,
        ]

        attributes_dict["personal_values_10"] = personal_values_10
        attributes_dict["personal_values_19"] = personal_values_19

        conservative = attributes_dict["data_properties"]["conservative"]
        liberal = attributes_dict["data_properties"]["liberal"]
        # Hard coded order! Conservative first, liberal second.
        attributes_dict["political_value"] = [conservative, liberal]
        # if there are multiple of the nested classes associated with the node in the ontology, code ensures it doesn't overwrite the other class.

        G.add_nodes_from([(node, attributes_dict)])

        # the if statement is needed to avoid the Restriction objects
        # still don't know why Restriction Objects are in our ontology!
        # technically each class could have multiple labels, but this way just pulling 1st label


def set_edge_properties(G):
    """Add edge annotation properties that exist on both nodes of an edge
    and create a list of properties to remove from the nodes.
    (Only source properties that exist on both nodes of an edge are only for the edge)

    Parameters
    ----------
    G: A networkx Graph
    """
    source_types = [
        "dc_source",
        "schema_academicBook",
        "schema_academicSourceNoPaywall",
        "schema_academicSourceWithPaywall",
        "schema_governmentSource",
        "schema_mediaSource",
        "schema_mediaSourceForConservatives",
        "schema_organizationSource",
    ]

    to_remove = {}
    for edge in list(G.edges):
        node_a = edge[0]
        node_b = edge[1]
        edge_attributes_dict = {}

        if (
            G[node_a][node_b]["type"]
            != "is_inhibited_or_prevented_or_blocked_or_slowed_by"
        ):

            for prop in G.nodes[node_a]["properties"].keys():
                if (
                    prop in source_types
                ):  # ensures only the source_types above are considered
                    node_a_prop_sources = set(G.nodes[node_a]["properties"][prop])
                    node_b_prop_sources = set(G.nodes[node_b]["properties"][prop])
                    intersection = node_a_prop_sources & node_b_prop_sources

                    # add intersection to edge property dictionary, ensuring if items already exist for that key, then they are added to the list
                    if intersection:
                        edge_attributes_dict[prop] = list(intersection)

                        if (node_a, prop) in to_remove.keys():
                            to_remove[(node_a, prop)] = (
                                to_remove[(node_a, prop)] | intersection
                            )
                        else:
                            to_remove[(node_a, prop)] = intersection

                        if (node_b, prop) in to_remove.keys():
                            to_remove[(node_b, prop)] = (
                                to_remove[(node_b, prop)] | intersection
                            )
                        else:
                            to_remove[(node_b, prop)] = intersection

        # add edge_attributes_dict to edge
        G.add_edge(node_a, node_b, properties=edge_attributes_dict)

        # alternative way of adding attributes to edges is commented out below:
        # nx.set_edge_attributes(
        #     G,
        #     {(node_a,node_b): edge_attributes_dict},
        #     "properties",
        # )

    return to_remove


def remove_edge_properties_from_nodes(G, to_remove):
    """Remove sources from properties from Networkx nodes when those sources occur on both nodes of an edge
    (because it marks that property is only for the edge).

    Parameters
    ----------
    G: A networkx graph
    to_remove: A dictionary of nodes and properties
    """
    for item in to_remove:
        # the node to remove sources from
        node = item[0]

        # the property type that has sources to remove
        prop = item[1]

        # the list of actual sources to remove
        sources_before_removing = set(G.nodes[node]["properties"][prop])
        sources_after_removing = list(sources_before_removing - to_remove[item])
        G.nodes[node]["properties"][prop] = sources_after_removing


def make_acyclic(G):
    """
    Converts a climate mind graph into an acyclic version by removing all the feedback loop edges.
    Paramater:
    G = Networkx graph (Climate Mind graph) created from converting webprotege OWL ontology to networkx graph using functions in make_graph.py
    """
    B = G.copy()
    # identify nodes that are in the class 'feedback loop' then remove those nodes' 'caueses' edges because they start feedback loops.
    # nx.get_node_attributes(B, "direct classes")
    feedback_nodes = list()
    graph_attributes_dictionary = nx.get_node_attributes(B, "direct classes")

    for node in graph_attributes_dictionary:
        if "feedback loop" in graph_attributes_dictionary[node]:
            feedback_nodes.append(node)
    # get the 'causes' edges that lead out of the feedback_nodes
    # must only remove edges that cause increase in greenhouse gases... so only remove edges if the neighbor is of the class 'increase in atmospheric greenhouse gas'
    feedbackloop_edges = list()
    for node in feedback_nodes:
        node_neighbors = B.neighbors(node)
        for neighbor in node_neighbors:
            if (
                "increase in atmospheric greenhouse gas"
                in graph_attributes_dictionary[neighbor]
                or "root cause linked to humans"
                in graph_attributes_dictionary[neighbor]
            ):
                # should make this 'increase in atmospheric greenhouse gas' not hard coded!
                if (
                    B[node][neighbor]["type"] == "causes_or_promotes"
                ):  # should probably make this so the causes_or_promotes isn't hard coded!
                    feedbackloop_edges.append((node, neighbor))

    # remove all the feedback loop edges
    for feedbackloopEdge in feedbackloop_edges:
        nodeA = feedbackloopEdge[0]
        nodeB = feedbackloopEdge[1]
        B.remove_edge(nodeA, nodeB)

    return B


def causal_parents(node, graph):
    """
    Returns the nodes (string names) that are causal parents of the node (have the edge type "causes_or_promotes"), else returns empty list.

    Parameters
    node - name of the node (string)
    graph - networkx graph object
    """
    node_causal_parents = []
    if list(graph.predecessors(node)):
        possibleCausalParents = graph.predecessors(node)
        for possibleCausalParent in possibleCausalParents:
            if graph[possibleCausalParent][node]["type"] == "causes_or_promotes":
                node_causal_parents.append(possibleCausalParent)
    return node_causal_parents


def local_graph(node, graph, visited_dictionary):
    """
    Recursive function that modifies a graph node amd all the upstream parents based on if the climate change node could possibly be a local concept for the user.
    Requires the graph to have 'isPossiblyLocal' filled in with 0 or 1 based on the results of the Location Relevance Flag values.

    Parameters:
    node - node name (string) of a node in the graph
    graph - networkx graph object (MUST BE ACYCLIC!!!)
    visited_dictionary - dictionary of which nodes have been visited by the local_graph

    returns:
    0 or 1 (the value for isPossiblyLocal for the node)
    """
    if node in visited_dictionary.keys() and "isPossiblyLocal" in graph.nodes[node]:
        return graph.nodes[node]["isPossiblyLocal"]
    else:
        visited_dictionary[node] = True

    if not causal_parents(node, graph):
        nx.set_node_attributes(
            graph,
            {node: 0},
            "isPossiblyLocal",
        )
        return graph.nodes[node]["isPossiblyLocal"]
    else:
        if "isPossiblyLocal" in graph.nodes[node] and isinstance(
            graph.nodes[node]["isPossiblyLocal"], int
        ):
            [
                local_graph(parent, graph, visited_dictionary)
                for parent in causal_parents(node, graph)
            ]
            return graph.nodes[node]["isPossiblyLocal"]
        else:
            parentLabels = [
                local_graph(parent, graph, visited_dictionary)
                for parent in causal_parents(node, graph)
            ]
            nx.set_node_attributes(
                graph,
                {node: any(parentLabels)},
                "isPossiblyLocal",
            )
            return graph.nodes[node]["isPossiblyLocal"]


# Returns the subgraph achieved by BFS on start_node
def custom_bfs(graph, start_node, direction="forward", edge_type="causes_or_promotes"):
    """
    Explores graph and gets the subgraph containing all the nodes that are reached via BFS from start_node

    Parameters
    ----------
    graph - nx.DiGraph to explore
    start_node - root of the BFS search
    direction - forward, reverse, or any. Controls what direction BFS searches in
    edge_type - only explore along edges of this type (can be "any")

    Returns
    -------
    subgraph with nodes explored
    """
    # Using a list because we want to have the explored elements returned later.
    queue = [start_node]
    cur_index = 0

    def do_bfs(element):
        nonlocal cur_index
        if direction == "reverse" or direction == "any":
            for start, end, type in graph.in_edges(element, "type"):
                if start not in queue and (edge_type == "any" or type == edge_type):
                    queue.append(start)
        if direction == "forward" or direction == "any":
            for start, end, type in graph.out_edges(element, "type"):
                if end not in queue and (edge_type == "any" or type == edge_type):
                    queue.append(end)

    do_bfs(start_node)

    while cur_index < len(queue):
        do_bfs(queue[cur_index])
        cur_index = cur_index + 1

    return graph.subgraph(queue)


def annotate_graph_with_problems(graph):
    """
    Annotates a graph with information needed for visualization. For example, which nodes are solutions, risks. Which
    nodes have long descriptions, sources. Which edges have sources.

    Parameters
    ----------
    graph - the graph to annotate (modifies the graph)
    """

    for start, end, data in graph.edges(data=True):
        edge_attr = graph.edges[start, end]

        # cyto_classes attribute is simply a placeholder.
        # We'll convert all elements from cyto_classes to cytoscape.js classes in visualize.py script
        edge_attr["cyto_classes"] = []
        if "risk solution" in graph.nodes[start] or "risk solution" in graph.nodes[end]:
            edge_attr["cyto_classes"].append("solution-edge")
        elif not data["properties"]:
            # Edge is not connecting to risk solution! Check if it has sources.
            edge_attr["cyto_classes"].append("edge-no-source")

    # Extract x y positions using graphviz dot algo. Use x,y positions to make cytoscape graph
    # Also doing some preprocessing
    for node, data in graph.nodes(data=True):

        graph.nodes[node]["cyto_classes"] = []

        risk_or_personal_value_node = False
        if "risk solution" in data:
            graph.nodes[node]["cyto_classes"].append("risk-solution")

        if any(data["personal_values_10"]):
            graph.nodes[node]["cyto_classes"].append("personal-value")

        if risk_or_personal_value_node:
            if data.get("properties", {}).get("schema_longDescription", ""):
                graph.nodes[node]["cyto_classes"].append("no-long-description")

            for source in SOURCE_TYPES:
                if data["properties"][source]:
                    graph.nodes[node]["cyto_classes"].append("node-no-sources")


# Joins subgraphs into a bigger subgraph
# We can't use nx.union because it doesn't add edges connecting two subgraphs together
def union_subgraph(subgraphs, *, base_graph):
    """
    Joins multiple subgraphs of the same base graph together. Edges connecting subgraphs are also included
    (whereas nx.union doesn't include edges connecting subgraphs together).

    Parameters
    ----------
    subgraphs - a list of subgraphs to union
    base_graph - forced keyword argument of the graph that these subgraphs are based upon

    Returns
    -------
    a new subgraph of base_graph containing all nodes in subgraphs list
    """
    G_node_set = set()
    for other_subg in subgraphs:
        G_node_set = G_node_set.union(set(other_subg.nodes()))
    return base_graph.subgraph(G_node_set)


def makeGraph(onto_path, edge_path, output_folder_path="."):
    """
    Main function to make networkx graph object from reference ontology and edge list.

    input: args = args from the argument parser for the function
                    (refOntologyPath, refEdgeListPath)
    output: saves a python pickle file of the networkx object, and yaml and json of the networkx object
    """

    # Load ontology and format object properties and annotation properties into Python readable names
    my_world = owlready2.World()
    onto = my_world.get_ontology(onto_path).load()
    obj_properties = list(onto.object_properties())
    annot_properties = list(onto.annotation_properties())
    data_properties = list(onto.data_properties())
    [give_alias(x) for x in obj_properties if x.label]
    [give_alias(x) for x in annot_properties if x.label]
    [give_alias(x) for x in data_properties if x.label]

    # run automated reasoning.
    with onto:
        sync_reasoner()


    # Read in the triples data
    ## DMARX - csv via make_network.outputEdges()
    #          via node_network.result
    # ... If we've already processed the ontology through the Network object,
    # why do we need to reload it here?
    # Can we move add_ontology_data_to_graph_nodes to network_class?
    df_edges = pd.read_csv(edge_path)

    G = nx.DiGraph()
    for src, tgt, kind in df_edges.values:
        G.add_edge(src, tgt, type=kind, properties=None)

    add_ontology_data_to_graph_nodes(G, onto)
    to_remove = set_edge_properties(G)
    remove_edge_properties_from_nodes(G, to_remove)

    # process the mitigation and adaptation solutions in the networkx object and add them into special attribute fields for each node for easy access in later for the API

    B = make_acyclic(G)
    all_myths = list(nx.get_node_attributes(B, "myth").keys())

    # Copy B to make annotations specific to visualizations
    B_annotated = B.copy()

    # Remove myths.Not necessary to visualize
    B_annotated.remove_nodes_from(myth for myth in all_myths)
    annotate_graph_with_problems(B_annotated)

    # Does the same thing. Assert to check correctness
    # Maybe we can replace with my implementation because I'd need the subgraph AND the nodes list anyways
    subgraph_upstream = custom_bfs(
        B_annotated, "increase in greenhouse effect", "reverse"
    ).copy()

    nodes_upstream_greenhouse_effect = list(subgraph_upstream.nodes())
    # now get all the nodes that have the inhibit relationship with the nodes found in nodes_upstream_greenhouse_effect (these nodes should all be the mitigation solutions)
    mitigation_solutions = list()

    # Iterates through all edges incident to nodes in upstream_greenhouse_effect
    for start, end, type in B.out_edges(nodes_upstream_greenhouse_effect, "type"):
        if type == "is_inhibited_or_prevented_or_blocked_or_slowed_by":
            mitigation_solutions.append(end)

    mitigation_solutions = list(set(mitigation_solutions))
    subgraph_mitigation = B_annotated.subgraph(mitigation_solutions)

    # sort the mitigation solutions from highest to lowest CO2 Equivalent Reduced / Sequestered (2020–2050)
    # in Gigatons from Project Drawdown scenario 2

    mitigation_solutions_with_co2 = dict()
    mitigation_solutions_no_co2 = []

    for solution in mitigation_solutions:
        if (
            solution not in mitigation_solutions_with_co2
            and G.nodes[solution]["data_properties"]["CO2_eq_reduced"]
        ):
            mitigation_solutions_with_co2[solution] = G.nodes[solution][
                "data_properties"
            ]["CO2_eq_reduced"]
        elif solution not in mitigation_solutions_no_co2:
            mitigation_solutions_no_co2.append(solution)

    mitigation_solutions_co2_sorted = sorted(
        mitigation_solutions_with_co2,
        key=mitigation_solutions_with_co2.get,
        reverse=True,
    )

    mitigation_solutions_co2_sorted.extend(mitigation_solutions_no_co2)

    mitigation_solutions = mitigation_solutions_co2_sorted

    # update the networkx object to have a 'mitigation solutions' field and include in it all nodes from mitigation_solutions
    nx.set_node_attributes(
        G,
        {"increase in greenhouse effect": mitigation_solutions},
        "mitigation solutions",
    )

    # add solution sources field to all mitigation solution nodes
    for solution in mitigation_solutions:
        sources = solution_sources(G.nodes[solution], SOURCE_TYPES)
        if sources:
            nx.set_node_attributes(
                G,
                {solution: sources},
                "solution sources",
            )

    # to check or obtain the solutions from the networkx object: G.nodes['increase in greenhouse effect']['mitigation solutions']

    # code to get the adaptation solutions from a node in the networkx object:

    # use the pruned copy of the graph (use B) because it has the feedback loop edges removed.
    # Get the upstream edges of the node in the B graph that occur between the node in question and the node 'increase in greenhouse effect'
    # print(list(nx.dfs_edges(B,”starting node name”))) #this is to get downstream edges
    # to do this could remove the parent edges of the 'increase in greenhouse effect' node?
    # adaptation is defined as solutions to the node or any node upstream of the node up until the node 'increase in greenhouse effect'.

    # get all the nodes that are downstream of 'increase in greenhouse effect'. should be all the impact/effect node... could probably get these by doing class search too
    # also includes nodes that are "has exposure dependencies of, like "person is in the marines", 'person is in a community likely without air conditioning', 'person is elderly'
    # so not exclusive to risks + adaptations.
    # This subgraph also contains cytoscape annotations (like cyto_classes), so shouldn't query the properties as they are not reflective of webprotege.
    subgraph_downstream_adaptations = custom_bfs(
        B_annotated, "increase in greenhouse effect", edge_type="any"
    ).copy()

    # The only difference between subgraph_downstream_adaptations and subgraph_downstream is that my
    # subgraph_downstream excludes all adaptation solutions.
    # Only "causation" edges would exclude "person is elderly" or "person is outside often"
    subgraph_downstream = custom_bfs(
        B_annotated, "increase in greenhouse effect", edge_type="causes_or_promotes"
    ).copy()

    total_adaptation_nodes = []
    for effectNode in subgraph_downstream_adaptations.nodes():
        intermediate_nodes = nx.all_simple_paths(
            B, "increase in greenhouse effect", effectNode
        )
        # collapse nested lists and remove duplicates
        intermediate_nodes = [
            item for sublist in intermediate_nodes for item in sublist
        ]
        intermediate_nodes = list(
            dict.fromkeys(intermediate_nodes)
        )  # gets unique nodes
        node_adaptation_solutions = list()
        for intermediateNode in intermediate_nodes:
            node_neighbors = G.neighbors(intermediateNode)
            for neighbor in node_neighbors:
                if (
                    G[intermediateNode][neighbor]["type"]
                    == "is_inhibited_or_prevented_or_blocked_or_slowed_by"
                ):  # bad to hard code in 'is_inhibited_or_prevented_or_blocked_or_slowed_by'
                    node_adaptation_solutions.append(neighbor)
                # if (
                #     G[intermediateNode][neighbor]["type"]
                #     == "myth_associated_with"
                # ):  # bad to hard code in 'myth_associated_with'
                #     node_myths.append(neighbor)
        # add the adaptation solutions to the networkx object for the node
        # be sure that solutions don't show up as effectNodes! and that they aren't solutions to themself! the code needs to be changed to avoid this.
        # ^solutions shouldn't be added as solutions to themself!
        node_adaptation_solutions = list(
            OrderedDict.fromkeys(node_adaptation_solutions)
        )  # gets unique nodes
        # print(str(effectNode)+": "+str(node_adaptation_solutions))

        # need to add a check here that doesn't add to effectNode attributes the effectNode as an adaptation solution (solution nodes should have themself as an adaptation solution!)
        nx.set_node_attributes(
            G, {effectNode: node_adaptation_solutions}, "adaptation solutions"
        )

        # add solution sources field to all adaptation solution nodes
        for solution in node_adaptation_solutions:
            sources = solution_sources(G.nodes[solution], SOURCE_TYPES)
            nx.set_node_attributes(
                G,
                {solution: sources},
                "solution sources",
            )
        total_adaptation_nodes.extend(node_adaptation_solutions)

    subgraph_adaptations = B_annotated.subgraph(total_adaptation_nodes).copy()

    subgraph_upstream_mitigations = union_subgraph(
        [subgraph_upstream, subgraph_mitigation], base_graph=B_annotated
    ).copy()

    # Computes an array of elements + nodes to input into cytoscape.js for each personal value
    # Computes the subgraphs achieved by BFS through each of those personal values

    personal_values = [
        label
        for label, pv_ranking in G.nodes.data("personal_values_10", [None])
        if any(pv_ranking)
    ]

    # Uncomment to reduce number of cases for faster debug.
    # personal_values = ['increase in physical violence']

    graph_downstream_adaptations_pv = dict.fromkeys(personal_values)

    # Make a temporary graph with reversed solutions for easier BFS
    G_slns_reversed = subgraph_downstream_adaptations.copy()

    # Modifying edge data while iterating. Have to get list before we iterate.
    g_edges = list(G_slns_reversed.edges(data=True))
    for start, end, data in g_edges:
        if subgraph_adaptations.has_node(end):
            G_slns_reversed.add_edge(end, start, **data)
            G_slns_reversed.remove_edge(start, end)
    for value_key in personal_values:
        subtree = custom_bfs(
            G_slns_reversed, value_key, direction="reverse", edge_type="any"
        )
        graph_downstream_adaptations_pv[value_key] = subtree.copy()

    # Total graphs exported for visualization:
    # subgraph_upstream_mitigations
    # subgraph_downstream_adaptations
    # subgraph_upstream
    # subgraph_downstream
    #
    # graph_data: dict of 21 personal values and the graph of risks leading to that personal value
    # graph_data_slns: same as graph_data except there are adaptation solutions added.

    with open(output_folder_path + "/graphs_for_visualization.pickle", "wb") as f:
        pickle.dump(
            dict(
                upstream_mitigations=subgraph_upstream_mitigations,
                downstream_adaptations=subgraph_downstream_adaptations,
                upstream=subgraph_upstream,
                downstream=subgraph_downstream,
                **graph_downstream_adaptations_pv
            ),
            f,
        )

    # process myths in networkx object to be easier for API
    general_myths = list()

    for myth in all_myths:
        node_neighbors = G.neighbors(myth)
        for neighbor in node_neighbors:
            if G[myth][neighbor]["type"] == "is_a_myth_about":

                impact_myths = []

                if "risk solution" in G.nodes[neighbor].keys():
                    if "solution myths" not in G.nodes[neighbor].keys():
                        solution_myths = []
                    else:
                        solution_myths = G.nodes[neighbor]["solution myths"]
                    solution_myths.append(myth)
                    nx.set_node_attributes(
                        G, {neighbor: solution_myths}, "solution myths"
                    )
                if subgraph_downstream_adaptations.has_node(neighbor):
                    if "impact myths" not in G.nodes[neighbor].keys():
                        impact_myths = []
                    else:
                        impact_myths = G.nodes[neighbor]["impact myths"]
                    impact_myths.append(myth)
                    nx.set_node_attributes(G, {neighbor: impact_myths}, "impact myths")
                if neighbor in nodes_upstream_greenhouse_effect:
                    general_myths.append(myth)
        # process myth sources into nice field called 'myth sources' with only unique urls from any source type
        myth_sources = list()
        for source_type in SOURCE_TYPES:
            if (
                "properties" in G.nodes[myth]
                and source_type in G.nodes[myth]["properties"]
            ):
                myth_sources.extend(G.nodes[myth]["properties"][source_type])

        myth_sources = list(
            OrderedDict.fromkeys(myth_sources)
        )  # removes any duplicates while preserving order
        nx.set_node_attributes(
            G,
            {myth: myth_sources},
            "myth sources",
        )

    # get unique general myths
    general_myths = list(dict.fromkeys(general_myths))

    # sort the myths by popularity (skeptical science)
    general_myths_dict = dict()

    for myth in general_myths:
        general_myths_dict[myth] = G.nodes[myth]["data_properties"]["myth_frequency"]

    general_myths_sorted = sorted(
        general_myths_dict,
        key=general_myths_dict.get,
        reverse=True,
    )

    general_myths = general_myths_sorted

    # update the networkx object to have a 'general myths' field and include in it all nodes from mitigation_solutions
    nx.set_node_attributes(
        G,
        {"increase in greenhouse effect": general_myths},
        "general myths",
    )

    # to check or obtain the solutions from the networkx object: G.nodes[node]['adaptation solutions']
    # ex: G.nodes['decrease in test scores']['adaptation solutions']
    # should probably code in for the 'adaptation solutions' field to read "None yet curated" if there isn't any to avoid errors from occuring later by API ?
    # G.nodes['increase in area burned by wildfire']['adaptation solutions'] should not return *** KeyError: 'adaptation solutions'

    # B.nodes['permafrost melt']['direct classes']

    # process and add sources (sources needed for effects, solutions, and myths)

    # get causal sources... function to get the causal edge sources for a specific node...
    for target_node in G.nodes:
        # get list nodes that have a relationship with the target node (are neighbor nodes), then filter it down to just the nodes with the causal relationship with the target node
        causal_sources = list()
        predecessor_nodes = G.predecessors(target_node)
        for predecessor_node in predecessor_nodes:
            if G[predecessor_node][target_node]["type"] == "causes_or_promotes":
                if G[predecessor_node][target_node]["properties"]:
                    causal_sources.append(
                        G[predecessor_node][target_node]["properties"]
                    )

        if causal_sources:
            # collapse down to just list of unique urls. strips off the type of source and the edge it originates from

            sources_list = list()

            for sources_dict in causal_sources:
                for key in sources_dict:
                    if key in SOURCE_TYPES:
                        sources_list.extend(sources_dict[key])

            # remove duplicate urls
            sources_list = list(dict.fromkeys(sources_list))

            # remove urls that aren't active or aren't real
            sources_list = [url for url in sources_list if validators.url(url)]

            nx.set_node_attributes(
                G,
                {target_node: sources_list},
                "causal sources",
            )

    # output_folder_path = "../PUT_NEW_OWL_FILE_IN_HERE/"
    save_graph_to_pickle(G, output_folder_path)

    T = G.copy()

    valid_test_ont = get_valid_test_ont()
    not_test_ont = get_non_test_ont()
    get_test_ontology(T, valid_test_ont, not_test_ont)

    save_test_ontology_to_json(T, output_folder_path)


def main(args):
    """
    Main function to make networkx graph object from reference ontology and edge list.

    input: args = args from the argument parser for the function
    (refOntologyPath, refEdgeListPath)
    output: saves a python pickle file of the networkx object, and yaml and json of the networkx object

    example: python3 make_graph.py "./climate_mind_ontology20200721.owl" "output.csv"
    """

    # set arguments
    onto_path = args.refOntologyPath
    edge_path = args.refEdgeListPath

    # run makeGraph function
    # Doesn't set path? I have to add default argument for path for this to work.
    makeGraph(onto_path, edge_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="get networkx graph object from ontology after running make_network.py"
    )
    parser.add_argument(
        "refOntologyPath", type=str, help="path to reference OWL2 ontology"
    )
    parser.add_argument(
        "refEdgeListPath",
        type=str,
        help="path for csv file of result edges (list of object,subject,predicate triples)",
    )

    args = parser.parse_args()
    main(args)
