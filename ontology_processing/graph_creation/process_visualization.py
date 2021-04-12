class ProcessVisualization:

    def __init__(self, graph):
        self.subgraph_upstream_mitigations = subgraph_upstream_mitigations
        self.subgraph_downstream_adaptations = subgraph_downstream_adaptations
        self.subgraph_upstream = subgraph_upstream
        self.subgraph_downstream = subgraph_downstream
        self.graph_downstream_adaptations_pv = graph_downstream_adaptations_pv

    def save_output(self):
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