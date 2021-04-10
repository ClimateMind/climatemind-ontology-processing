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
    from graph_creation.graph_utils import custom_bfs
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
    from ontology_processing.graph_creation.graph_utils import custom_bfs

class ProcessVisualization:

    def __init__(self, graph):
        self.graph = make_acyclic(graph)
        self.subgraph_upstream = None
        self.subgraph_mitigation = None

    def remove_myths(self, G):
        """
        Myths are not used for visualization.
        """
        all_myths = list(nx.get_node_attributes(self.graph, "myth").keys())
        self.graph.remove_nodes_from(myth for myth in all_myths)

    def annotate_graph_with_problems(self):
        """
        Annotates a graph with information needed for visualization. For example, which nodes are solutions, risks. Which
        nodes have long descriptions, sources. Which edges have sources.
        Parameters
        ----------
        graph - the graph to annotate (modifies the graph)
        """

        for start, end, data in self.graph.edges(data=True):
            edge_attr = self.graph.edges[start, end]

            # cyto_classes attribute is simply a placeholder.
            # We'll convert all elements from cyto_classes to cytoscape.js classes in visualize.py script
            edge_attr["cyto_classes"] = []
            if "risk solution" in self.graph.nodes[start] or "risk solution" in self.graph.nodes[end]:
                edge_attr["cyto_classes"].append("solution-edge")
            elif not data["properties"]:
                # Edge is not connecting to risk solution! Check if it has sources.
                edge_attr["cyto_classes"].append("edge-no-source")

        # Extract x y positions using graphviz dot algo. Use x,y positions to make cytoscape graph
        # Also doing some preprocessing
        for node, data in self.graph.nodes(data=True):

            self.graph.nodes[node]["cyto_classes"] = []

            risk_or_personal_value_node = False
            if "risk solution" in data:
                self.graph.nodes[node]["cyto_classes"].append("risk-solution")

            if any(data["personal_values_10"]):
                self.graph.nodes[node]["cyto_classes"].append("personal-value")

            if risk_or_personal_value_node:
                if data.get("properties", {}).get("schema_longDescription", ""):
                    self.graph.nodes[node]["cyto_classes"].append("no-long-description")

                for source in SOURCE_TYPES:
                    if data["properties"][source]:
                        self.graph.nodes[node]["cyto_classes"].append("node-no-sources")

    def create_subgraph(self):
        """Grabs a subgraph of the 'increase in greenhouse effect' tree"""
        self.subgraph_upstream = custom_bfs(
            self.graph, "increase in greenhouse effect", "reverse"
        ).copy()

    def create_mitigations(self):
        """
        Get all the nodes that have the inhibit relationship with the nodes
        found in nodes_upstream_greenhouse_effect (these nodes should all be
        the mitigation solutions).
        """
        nodes_upstream_greenhouse_effect = list(self.subgraph_upstream.nodes())
        mitigation_solutions = list()

        # Iterates through all edges incident to nodes in upstream_greenhouse_effect
        for start, end, type in B.out_edges(nodes_upstream_greenhouse_effect, "type"):
            if type == "is_inhibited_or_prevented_or_blocked_or_slowed_by":
                mitigation_solutions.append(end)

        mitigation_solutions = list(set(mitigation_solutions))
        self.subgraph_mitigation = self.graph.subgraph(mitigation_solutions)