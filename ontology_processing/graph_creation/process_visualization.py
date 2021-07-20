import pickle

from graph_creation.ontology_processing_utils import custom_bfs, union_subgraph

class ProcessVisualization:

    """
    Creates a Pickle Dump of Annotated Subgraphs used 
    for the Visualization Dashboards in the Climatemind-Analytics Repo.
    """

    def __init__(self, annotated_graph):
        self.annotated_graph = annotated_graph
        self.subgraph_upstream_mitigations = None
        self.subgraph_downstream_adaptations = None
        self.subgraph_upstream = custom_bfs(
            self.annotated_graph, "increase in greenhouse effect", "reverse"
        ).copy()
        self.subgraph_downstream = None
        self.graph_downstream_adaptations_pv = None

    def save_output(self, output_folder_path):
        with open(output_folder_path + "/graphs_for_visualization.pickle", "wb") as f:
            pickle.dump(
                dict(
                    upstream_mitigations=self.subgraph_upstream_mitigations,
                    downstream_adaptations=self.subgraph_downstream_adaptations,
                    upstream=self.subgraph_upstream,
                    downstream=self.subgraph_downstream,
                    **self.graph_downstream_adaptations_pv
                ),
                f,
        )

    def annotate_graph_with_problems(self):
        """
        Annotates a graph with information needed for visualization. 
        For example, which nodes are solutions, risks. Which
        nodes have long descriptions, sources. Which edges have sources.
        """
        for start, end, data in self.annotated_graph.edges(data=True):
            edge_attr = self.annotated_graph.edges[start, end]

            # cyto_classes attribute is simply a placeholder.
            # We'll convert all elements from cyto_classes to cytoscape.js classes in visualize.py script
            edge_attr["cyto_classes"] = []
            if "risk solution" in self.annotated_graph.nodes[start] or "risk solution" in self.annotated_graph.nodes[end]:
                edge_attr["cyto_classes"].append("solution-edge")
            elif not data["properties"]:
                # Edge is not connecting to risk solution! Check if it has sources.
                edge_attr["cyto_classes"].append("edge-no-source")

        # Extract x y positions using graphviz dot algo. Use x,y positions to make cytoscape graph
        # Also doing some preprocessing
        for node, data in self.annotated_graph.nodes(data=True):

            self.annotated_graph.nodes[node]["cyto_classes"] = []

            risk_or_personal_value_node = False
            if "risk solution" in data:
                self.annotated_graph.nodes[node]["cyto_classes"].append("risk-solution")

            if any(data["personal_values_10"]):
                self.annotated_graph.nodes[node]["cyto_classes"].append("personal-value")

            if risk_or_personal_value_node:
                if data.get("properties", {}).get("schema_longDescription", ""):
                    self.annotated_graph.nodes[node]["cyto_classes"].append("no-long-description")

                for source in SOURCE_TYPES:
                    if data["properties"][source]:
                        self.annotated_graph.nodes[node]["cyto_classes"].append("node-no-sources")


    def get_subgraphs(self, total_adaptation_nodes, mitigation_solutions):
        """
        Get all the nodes that are downstream of 'increase in greenhouse effect'. 
        should be all the impact/effect node... could probably get these by doing 
        a class search too. Also includes nodes that are "has exposure dependencies of", 
        like "person is in the marines", 'person is in a community likely without air conditioning', or
        'person is elderly' so not exclusive to risks + adaptations.
        This subgraph also contains cytoscape annotations (like cyto_classes), 
        so shouldn't query the properties as they are not reflective of webprotege.
        """

        subgraph_mitigation = self.annotated_graph.subgraph(mitigation_solutions)

        self.subgraph_downstream_adaptations = custom_bfs(
            self.annotated_graph, "increase in greenhouse effect", edge_type="any"
        ).copy()

        # The only difference between subgraph_downstream_adaptations and subgraph_downstream is that my
        # subgraph_downstream excludes all adaptation solutions.
        # Only "causation" edges would exclude "person is elderly" or "person is outside often"
        self.subgraph_downstream = custom_bfs(
            self.annotated_graph, "increase in greenhouse effect", edge_type="causes_or_promotes"
        ).copy()

        subgraph_adaptations = self.annotated_graph.subgraph(total_adaptation_nodes).copy()

        self.subgraph_upstream_mitigations = union_subgraph(
            [self.subgraph_upstream, subgraph_mitigation], base_graph=self.annotated_graph
        ).copy()

        # Computes an array of elements + nodes to input into cytoscape.js for each personal value
        # Computes the subgraphs achieved by BFS through each of those personal values

        personal_values = [
            label
            for label, pv_ranking in self.annotated_graph.nodes.data("personal_values_10", [None]) #Possible change to G
            if any(pv_ranking)
        ]

        # Uncomment to reduce number of cases for faster debug.
        # personal_values = ['increase in physical violence']

        self.graph_downstream_adaptations_pv = dict.fromkeys(personal_values)

        # Make a temporary graph with reversed solutions for easier BFS
        G_slns_reversed = self.subgraph_downstream_adaptations.copy()

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
            self.graph_downstream_adaptations_pv[value_key] = subtree.copy()

    def get_downstream_adaptations(self):
        return self.subgraph_downstream_adaptations