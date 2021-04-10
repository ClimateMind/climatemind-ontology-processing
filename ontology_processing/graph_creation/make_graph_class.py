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

class MakeGraph:
    def __init__(self, onto_path, edge_path, output_folder_path="."):
        self.onto_path = onto_path
        self.edge_path = edge_path
        self.output_folder_path = output_folder_path
        self.onto = None
        self.object_properties = None
        self.annot_properties = None
        self.data_properties = None
        self.G = nx.DiGraph()

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

    B = make_acyclic(G)
    all_myths = list(nx.get_node_attributes(B, "myth").keys())







