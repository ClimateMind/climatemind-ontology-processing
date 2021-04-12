try:
    from graph_creation.ontology_processing_utils import (
        give_alias,
        save_test_ontology_to_json,
        save_graph_to_pickle,
        get_valid_test_ont,
        get_non_test_ont,
        remove_non_test_nodes,
        get_test_ontology,
        get_source_types,
    )
    from graph_creation.graph_utils import custom_bfs, solution_sources
except ImportError:
    from ontology_processing.graph_creation.ontology_processing_utils import (
        give_alias,
        save_test_ontology_to_json,
        save_graph_to_pickle,
        get_valid_test_ont,
        get_non_test_ont,
        remove_non_test_nodes,
        get_test_ontology,
        get_source_types,
    )
    from ontology_processing.graph_creation.graph_utils import custom_bfs, solution_sources

class MakeGraph:
    def __init__(self, onto_path, edge_path, output_folder_path="."):
        self.onto_path = onto_path
        self.edge_path = edge_path
        self.output_folder_path = output_folder_path
        self.onto = None
        self.object_properties = None
        self.annot_properties = None
        self.data_properties = None
        self.all_myths = None
        self.G = nx.DiGraph()
        self.B = None
        self.B_annotated = None
        self.subgraph_upstream = None

    def load_ontology(self):
        """
        Load the ontology from the OWL file specified by onto_path.
        """
        my_world = owlready2.World()
        self.onto = my_world.get_ontology(self.onto_path).load()

    def set_properties(self):
        """
        Format object properties and annotation properties into Python readable names.
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
        """
        with self.onto:
            sync_reasoner()

    def add_edges_to_graph(self):
        df_edges = pd.read_csv(self.edge_path)
        for src, tgt, kind in df_edges.values:
            self.G.add_edge(src, tgt, type=kind, properties=None)

    def build_attributes_dict(self):
        cm_class = self.onto.search_one(label="climate mind")
        superclasses = list(cm_class.subclasses())

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

        for node in list(self.G.nodes):
            ontology_node = self.onto.search_one(label=node)

            attributes_dict = {}
            self.add_basic_info(attributes_dict, ontology_node)
            self.add_classes(attributes_dict, ontology_node)
            self.add_properties(attributes_dict, ontology_node, annot_properties, data_properties)
            self.add_personal_values(attributes_dict)
            self.add_radical_political(attributes_dict)
            self.G.add_nodes_from([(node, attributes_dict)])

    def add_basic_info(self, attributes_dict, ontology_node):
        attributes_dict["label"] = str(ontology_node.label[0])
        attributes_dict["iri"] = str(ontology_node)
        attributes_dict["comment"] = str(ontology_node.comment)

    def add_classes(self, attributes_dict, ontology_node):
        """
        TODO: Kameron to add docstring (Please use simple explanation as class is a generic word)
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
            for super_class in superclasses:
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

    def make_annotated(self):
        """
        Create an annotated graph used for visualization
        """
        self.all_myths = list(nx.get_node_attributes(self.B, "myth").keys())

        # Copy B to make annotations specific to visualizations
        self.B_annotated = B.copy()

        # Myths not necessary to visualize
        self.B_annotated.remove_nodes_from(myth for myth in all_myths)

    def make_acyclic(self):
        """
        Converts a climate mind graph into an acyclic version by removing all the feedback loop edges.
        """
        self.B = G.copy()
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
        nodes_upstream_greenhouse_effect = list(self.subgraph_upstream.nodes())
        mitigation_solutions = list()

        # Iterates through all edges incident to nodes in upstream_greenhouse_effect
        for start, end, type in B.out_edges(nodes_upstream_greenhouse_effect, "type"):
            if type == "is_inhibited_or_prevented_or_blocked_or_slowed_by":
                mitigation_solutions.append(end)

        mitigation_solutions = list(set(mitigation_solutions))
        subgraph_mitigation = B_annotated.subgraph(mitigation_solutions)

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

        # update the networkx object to have a 'mitigation solutions' field
        # and include in it all nodes from mitigation_solutions
        nx.set_node_attributes(
            self.G,
            {"increase in greenhouse effect": mitigation_solutions},
            "mitigation solutions",
        )

        # add solution sources field to all mitigation solution nodes
        for solution in mitigation_solutions:
            sources = solution_sources(self.G.nodes[solution], SOURCE_TYPES)
            if sources:
                nx.set_node_attributes(
                    G,
                    {solution: sources},
                    "solution sources",
                )

    def annotate_graph_with_problems(self):
        """
        Annotates a graph with information needed for visualization. 
        For example, which nodes are solutions, risks. Which
        nodes have long descriptions, sources. Which edges have sources.
        """
        for start, end, data in self.B_annotated.edges(data=True):
            edge_attr = self.B_annotated.edges[start, end]

            # cyto_classes attribute is simply a placeholder.
            # We'll convert all elements from cyto_classes to cytoscape.js classes in visualize.py script
            edge_attr["cyto_classes"] = []
            if "risk solution" in self.B_annotated.nodes[start] or "risk solution" in self.B_annotated.nodes[end]:
                edge_attr["cyto_classes"].append("solution-edge")
            elif not data["properties"]:
                # Edge is not connecting to risk solution! Check if it has sources.
                edge_attr["cyto_classes"].append("edge-no-source")

        # Extract x y positions using graphviz dot algo. Use x,y positions to make cytoscape graph
        # Also doing some preprocessing
        for node, data in self.B_annotated.nodes(data=True):

            self.B_annotated.nodes[node]["cyto_classes"] = []

            risk_or_personal_value_node = False
            if "risk solution" in data:
                self.B_annotated.nodes[node]["cyto_classes"].append("risk-solution")

            if any(data["personal_values_10"]):
                self.B_annotated.nodes[node]["cyto_classes"].append("personal-value")

            if risk_or_personal_value_node:
                if data.get("properties", {}).get("schema_longDescription", ""):
                    self.B_annotated.nodes[node]["cyto_classes"].append("no-long-description")

                for source in SOURCE_TYPES:
                    if data["properties"][source]:
                        self.B_annotated.nodes[node]["cyto_classes"].append("node-no-sources")

    
    def create_subgraph(self):
        self.subgraph_upstream = custom_bfs(
            self.B_annotated, "increase in greenhouse effect", "reverse"
        ).copy()

    def get_subgraphs_for_viz(self):
        """
        Get all the nodes that are downstream of 'increase in greenhouse effect'. 
        should be all the impact/effect node... could probably get these by doing 
        a class search too. Also includes nodes that are "has exposure dependencies of", 
        like "person is in the marines", 'person is in a community likely without air conditioning', or
        'person is elderly' so not exclusive to risks + adaptations.
        This subgraph also contains cytoscape annotations (like cyto_classes), 
        so shouldn't query the properties as they are not reflective of webprotege.
        """
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
    
        return subgraph_upstream_mitigations, subgraph_downstream_adaptations, subgraph_upstream, subgraph_downstream, graph_downstream_adaptations_pv
        










