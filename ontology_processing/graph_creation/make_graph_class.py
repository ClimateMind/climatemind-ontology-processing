import pickle
import argparse
import networkx as nx
import pandas as pd
import validators

import owlready2
from owlready2 import sync_reasoner
from collections import OrderedDict

from graph_creation.ontology_processing_utils import (
    give_alias,
    save_test_ontology_to_json,
    save_graph_to_pickle,
    get_valid_test_ont,
    get_non_test_ont,
    remove_non_test_nodes,
    get_test_ontology,
    get_source_types,
    solution_sources,
    listify,
    union_subgraph,
)

class MakeGraph:

    """
    Takes an XML/RDF OWL file, extracts all of the nodes and relationships
    and loads these into a NetworkX Graph Object which is used for the Climatemind-Backend
    application.

    This complete graph contains all nodes from the Ontology, including Climate Issues, Myths, and Solutions
    which are used to populate the user feed in the user-facing application.

    There may be some benefit in splitting up this file into smaller chunks in the future, but for now this
    should be relatively digestible.
    """

    def __init__(self, onto_path, edge_path, output_folder_path="."):
        self.onto_path = onto_path
        self.edge_path = edge_path
        self.output_folder_path = output_folder_path
        self.onto = None
        self.object_properties = None
        self.annot_properties = None
        self.data_properties = None
        self.G = nx.DiGraph()
        self.B = None
        self.superclasses = None
        self.subgraph_mitigation = None

    def load_ontology(self):
        """
        Load the ontology from the OWL file specified by onto_path.
        """
        my_world = owlready2.World()
        self.onto = my_world.get_ontology(self.onto_path).load()

    def set_properties(self):
        """
        Format object properties and annotation properties into Python readable names, so
        they can be referenced in the rest of the code.
        """
        self.obj_properties = list(self.onto.object_properties())
        self.annot_properties = list(self.onto.annotation_properties())
        self.data_properties = list(self.onto.data_properties())
        [give_alias(x) for x in self.obj_properties if x.label]
        [give_alias(x) for x in self.annot_properties if x.label]
        [give_alias(x) for x in self.data_properties if x.label]

    def automate_reasoning(self):
        """
        Run automated reasoning

        OWL reasoners can be used to check the consistency of an ontology,
        and to deduce new fact in the ontology. Typically be reclassing Individuals to new Classes, 
        and Classes to new superclasses, depending on their relations.
        """
        # Set a lower JVM memory limit
        owlready2.reasoning.JAVA_MEMORY = 500
        with self.onto:
            sync_reasoner()

    def add_edges_to_graph(self):
        """
        Converts OWL file edges to NetworkX Graph Edges
        Edges are connections between two nodes
        """
        df_edges = pd.read_csv(self.edge_path)
        for src, tgt, kind in df_edges.values:
            self.G.add_edge(src, tgt, type=kind, properties=None)

    def build_attributes_dict(self):
        cm_class = self.onto.search_one(label="climate mind")
        self.superclasses = list(cm_class.subclasses())

        # get annotation properties for all objects of the ontology (whether node or class)
        annot_properties = [
            thing.label[0].replace(":", "_")
            for thing in list(self.onto.annotation_properties())
            if thing.label
        ]

        # get data properties for all objects of the ontology (whether node or class)
        data_properties = [
            thing.label[0].replace(" ", "_")
            for thing in list(self.onto.data_properties())
            if thing.label
        ]

        # Each node has an attributes dictionary that contains all of the data for that node.
        # Here we add all of these attributes to the dictionary
        for node in list(self.G.nodes):
            ontology_node = self.onto.search_one(label=node)

            attributes_dict = {}
            self.add_basic_info(attributes_dict, ontology_node)
            self.add_ontology_classes(attributes_dict, ontology_node)
            self.add_properties(attributes_dict, ontology_node, annot_properties, data_properties)
            self.add_personal_values(attributes_dict)
            self.add_radical_political(attributes_dict)
            self.G.add_nodes_from([(node, attributes_dict)])

    def add_basic_info(self, attributes_dict, ontology_node):
        attributes_dict["label"] = str(ontology_node.label[0])
        attributes_dict["iri"] = str(ontology_node)
        attributes_dict["comment"] = str(ontology_node.comment)

    def add_ontology_classes(self, attributes_dict, ontology_node):
        """
        Specifically, all the classes that node directly belongs to and all the ancestor nodes classes that the node should inherit.
        """
        class_objects = self.onto.get_parents_of(ontology_node)
        attributes_dict["direct classes"] = listify(class_objects, self.onto)
        all_classes = []
        for parent in class_objects:
            if parent in self.onto.classes():
                all_classes.extend(parent.ancestors())

        list_classes = listify(all_classes, self.onto)
        list_classes = list(set(list_classes))
        if "climate mind" in list_classes:
            list_classes.remove("climate mind")
        attributes_dict["all classes"] = list_classes

        # for each class in the classes associated with the node, list that class in the appropriate super_class in the attributes_dict and all of the ancestor classes of that class
        for node_class in class_objects:
            for super_class in self.superclasses:
                if node_class in super_class.descendants():
                    to_add = listify(node_class.ancestors(), self.onto)
                    if "climate mind" in to_add:
                        to_add.remove("climate mind")
                    if super_class in attributes_dict.keys():
                        attributes_dict[str(super_class.label[0])] = list(
                            set(attributes_dict[super_class]) | set(to_add)
                        )
                    else:
                        attributes_dict[str(super_class.label[0])] = to_add

    def add_properties(self, attributes_dict, ontology_node, annot_properties, data_properties):
        """
        Add annotation properties and data properties to the attributes_dict
        """
        attributes_dict["properties"] = {
            prop: list(getattr(ontology_node, prop)) for prop in annot_properties
        }

        attributes_dict["data_properties"] = {
            prop: getattr(ontology_node, prop) for prop in data_properties
        }

    def add_personal_values(self, attributes_dict):
        """
        Format personal_values_10 and personal_values_19 to facilitate easier
        scoring later by the climatemind-backend app.

        Each node is associated with personal values (for the user). If a node
        is tied to a personal value, it will be marked 1 otherwise 0.

        There are two personal value arrays corresponding to 10 and 19 values.
        These are hard coded in and the order is very important. The order is
        alphabetical by value name.

        The resulting arrays are added to the attributes_dict.
        """
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
        benevolence = self.compute(
            [
                attributes_dict["data_properties"]["benevolence_caring"],
                attributes_dict["data_properties"]["benevolence_dependability"],
            ]
        )
        conformity = self.compute(
            [
                attributes_dict["data_properties"]["conformity_interpersonal"],
                attributes_dict["data_properties"]["conformity_rules"],
            ]
        )
        hedonism = attributes_dict["data_properties"]["hedonism"]
        power = self.compute(
            [
                attributes_dict["data_properties"]["power_dominance"],
                attributes_dict["data_properties"]["power_resources"],
            ]
        )
        security = self.compute(
            [
                attributes_dict["data_properties"]["security_personal"],
                attributes_dict["data_properties"]["security_societal"],
            ]
        )
        self_direction = self.compute(
            [
                attributes_dict["data_properties"]["self-direction_autonomy_of_action"],
                attributes_dict["data_properties"][
                    "self-direction_autonomy_of_thought"
                ],
            ]
        )
        stimulation = attributes_dict["data_properties"]["stimulation"]
        tradition = attributes_dict["data_properties"]["tradition"]
        universalism = self.compute(
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

    def compute(self, values):
        """
        Collapse a vector potentially consisting of 0, 1, -1 and None to a single value.
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

    def add_radical_political(self, attributes_dict):
        """
        In order to prevent a backfire effect (user is persuaded AGAINST solutions),
        we want to avoid serving nodes with strong political ties that conflict
        with the user's political beliefs.

        These are in a hardcoded order (conservative first, liberal second). The
        order should not be changed as it's used by the climatemind-backend app.
        """
        conservative = attributes_dict["data_properties"]["conservative"]
        liberal = attributes_dict["data_properties"]["liberal"]
        attributes_dict["political_value"] = [conservative, liberal]

    def set_edge_properties(self):
        """
        Add edge annotation properties that exist on both nodes of an edge
        and create a list of properties to remove from the nodes.
        (Only source properties that exist on both nodes of an edge are only for the edge)
        """
        source_types = get_source_types()

        to_remove = {}
        for edge in list(self.G.edges):
            node_a = edge[0]
            node_b = edge[1]
            edge_attributes_dict = {}

            if (
                self.G[node_a][node_b]["type"]
                != "is_inhibited_or_prevented_or_blocked_or_slowed_by"
            ):

                for prop in self.G.nodes[node_a]["properties"].keys():
                    if (
                        prop in source_types
                    ):  # ensures only the source_types above are considered
                        node_a_prop_sources = set(self.G.nodes[node_a]["properties"][prop])
                        node_b_prop_sources = set(self.G.nodes[node_b]["properties"][prop])
                        intersection = node_a_prop_sources & node_b_prop_sources

                        # add intersection to edge property dictionary, ensuring if items already exist 
                        # for that key, then they are added to the list
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

            self.G.add_edge(node_a, node_b, properties=edge_attributes_dict)

        return to_remove


    def remove_edge_properties_from_nodes(self, to_remove):
        """
        Remove sources from properties from Networkx nodes when those sources occur on both nodes of an edge
        (because it marks that property is only for the edge).

        Parameters
        ----------
        to_remove: A dictionary of nodes and properties
        """
        for item in to_remove:
            # the node to remove sources from
            node = item[0]

            # the property type that has sources to remove
            prop = item[1]

            # the list of actual sources to remove
            sources_before_removing = set(self.G.nodes[node]["properties"][prop])
            sources_after_removing = list(sources_before_removing - to_remove[item])
            self.G.nodes[node]["properties"][prop] = sources_after_removing

    def get_graph(self):
        return self.G

    def get_annotated(self):
        """
        Create an annotated graph used for visualization
        """
        all_myths = list(nx.get_node_attributes(self.B, "myth").keys())

        # Copy B to make annotations specific to visualizations
        annotated_graph = self.B.copy()

        # Myths not necessary to visualize
        annotated_graph.remove_nodes_from(myth for myth in all_myths)

        return annotated_graph

    def make_acyclic(self):
        """
        Converts a climate mind graph into an acyclic version by removing all the feedback loop edges.
        """
        self.B = self.G.copy()
        # identify nodes that are in the class 'feedback loop' then remove 
        # those nodes' 'causes' edges because they start feedback loops.
        feedback_nodes = list()
        graph_attributes_dictionary = nx.get_node_attributes(self.B, "direct classes")

        for node in graph_attributes_dictionary:
            if "feedback loop" in graph_attributes_dictionary[node]:
                feedback_nodes.append(node)
        # get the 'causes' edges that lead out of the feedback_nodes
        # must only remove edges that cause increase in greenhouse gases... 
        # so only remove edges if the neighbor is of the class 'increase in atmospheric greenhouse gas'
        feedbackloop_edges = list()
        for node in feedback_nodes:
            node_neighbors = self.B.neighbors(node)
            for neighbor in node_neighbors:
                if (
                    "increase in atmospheric greenhouse gas"
                    in graph_attributes_dictionary[neighbor]
                    or "root cause linked to humans"
                    in graph_attributes_dictionary[neighbor]
                ):
                    # should make this 'increase in atmospheric greenhouse gas' not hard coded!
                    if (
                        self.B[node][neighbor]["type"] == "causes_or_promotes"
                    ):  # should probably make this so the causes_or_promotes isn't hard coded!
                        feedbackloop_edges.append((node, neighbor))

        # remove all the feedback loop edges
        for feedbackloopEdge in feedbackloop_edges:
            nodeA = feedbackloopEdge[0]
            nodeB = feedbackloopEdge[1]
            self.B.remove_edge(nodeA, nodeB)

    def get_mitigations(self):
        """
        Get all the nodes that have the inhibit relationship 
        with the nodes found in nodes_upstream_greenhouse_effect 
        (these nodes should all be the mitigation solutions)
        """
        # feedback loop edges should be severed in the graph copy B
        edges_upstream_greenhouse_effect = nx.edge_dfs(
            self.B, "increase in greenhouse effect", orientation="reverse"
        )

        nodes_upstream_greenhouse_effect = []
        for edge in edges_upstream_greenhouse_effect:
            node_a = edge[0]
            node_b = edge[1]
            if self.B[node_a][node_b]["type"] == "causes_or_promotes":
                nodes_upstream_greenhouse_effect.append(node_a)
                nodes_upstream_greenhouse_effect.append(node_b)

            # get unique ones
        nodes_upstream_greenhouse_effect = list(
            OrderedDict.fromkeys(nodes_upstream_greenhouse_effect)
        )  # this shouldn't include myths!
        mitigation_solutions = []

        # Iterates through all edges incident to nodes in upstream_greenhouse_effect
        for start, end, type in self.B.out_edges(nodes_upstream_greenhouse_effect, "type"):
            if type == "is_inhibited_or_prevented_or_blocked_or_slowed_by":
                mitigation_solutions.append(end)

        mitigation_solutions = list(set(mitigation_solutions))
        return mitigation_solutions, nodes_upstream_greenhouse_effect

    def add_mitigations(self, mitigation_solutions):
        """
        Sort the mitigation solutions from highest to lowest
        CO2 Equivalent Reduced / Sequestered (2020–2050)
        in Gigatons from Project Drawdown scenario 2.
        """

        mitigation_solutions_with_co2 = dict()
        mitigation_solutions_no_co2 = []

        for solution in mitigation_solutions:
            if (
                solution not in mitigation_solutions_with_co2
                and self.G.nodes[solution]["data_properties"]["CO2_eq_reduced"]
            ):
                mitigation_solutions_with_co2[solution] = self.G.nodes[solution][
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

        # update the networkx object to have a 'mitigation solutions' field
        # and include in it all nodes from mitigation_solutions
        nx.set_node_attributes(
            self.G,
            {"increase in greenhouse effect": mitigation_solutions},
            "mitigation solutions",
        )

        # add solution sources field to all mitigation solution nodes
        for solution in mitigation_solutions:
            sources = solution_sources(self.G.nodes[solution])
            if sources:
                nx.set_node_attributes(
                    self.G,
                    {solution: sources},
                    "solution sources",
                )

    def process_node_identity(self):
        downstream_nodes = nx.dfs_edges(self.B, "increase in greenhouse effect")
        downstream_nodes = [item for sublist in downstream_nodes for item in sublist]
        nodes_downstream_greenhouse_effect = list(OrderedDict.fromkeys(downstream_nodes))

        total_adaptation_nodes = []
        for effectNode in nodes_downstream_greenhouse_effect:
            intermediate_nodes = nx.all_simple_paths(
                self.B, "increase in greenhouse effect", effectNode
            )
            # collapse nested lists and remove duplicates
            intermediate_nodes = [
                item for sublist in intermediate_nodes for item in sublist
            ]
            intermediate_nodes = list(
                dict.fromkeys(intermediate_nodes)
            )  # gets unique nodes
            node_adaptation_solutions = []
            for intermediate_node in intermediate_nodes:
                node_neighbors = self.G.neighbors(intermediate_node)
                for neighbor in node_neighbors:
                    if (
                        self.G[intermediate_node][neighbor]["type"]
                        == "is_inhibited_or_prevented_or_blocked_or_slowed_by"
                    ):  # bad to hard code in 'is_inhibited_or_prevented_or_blocked_or_slowed_by'
                        node_adaptation_solutions.append(neighbor)
            node_adaptation_solutions = list(
                OrderedDict.fromkeys(node_adaptation_solutions)
            )  # gets unique nodes

            # need to add a check here that doesn't add to effectNode attributes the effectNode as an adaptation solution (solution nodes should have themself as an adaptation solution!)
            nx.set_node_attributes(
                self.G, {effectNode: node_adaptation_solutions}, "adaptation solutions"
            )

            # add solution sources field to all adaptation solution nodes
            for solution in node_adaptation_solutions:
                sources = solution_sources(self.G.nodes[solution])
                nx.set_node_attributes(
                    self.G,
                    {solution: sources},
                    "solution sources",
                )
            total_adaptation_nodes.extend(node_adaptation_solutions)
        return total_adaptation_nodes









