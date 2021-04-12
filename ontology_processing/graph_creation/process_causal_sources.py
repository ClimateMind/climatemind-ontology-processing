try:
    from graph_creation.ontology_processing_utils import (
        get_source_types,
    )
except ImportError:
    from ontology_processing.graph_creation.ontology_processing_utils import (
        get_source_types,
    )

class ProcessCausalSources:
    """
    TODO: Kameron to add docstring about what causal sources are
    """
    def __init__(self, G):
        self.G = G
        self.source_types = get_source_types()
    
    def process_sources(self):
        """
        Get causal sources from each node
        """
        for target_node in self.G.nodes:
            self.get_causal_relationships(target_node)

            if causal_sources:
                self.collapse_url()

    def get_causal_relationships(self, target_node):
        """
        Get list nodes that have a relationship with the target node (are neighbor nodes), 
        then filter it down to just the nodes with the causal relationship with the target node
        """
        causal_sources = list()
        predecessor_nodes = self.G.predecessors(target_node)
        for predecessor_node in predecessor_nodes:
            if self.G[predecessor_node][target_node]["type"] == "causes_or_promotes":
                if self.G[predecessor_node][target_node]["properties"]:
                    causal_sources.append(
                        self.G[predecessor_node][target_node]["properties"]
                    )

    def collapse_url(self):
        """
        Collapse down to just list of unique urls. Strips off the type of source
        and the edge it originates from
        """
        sources_list = list()

        for sources_dict in causal_sources:
            for key in sources_dict:
                if key in self.source_types:
                    sources_list.extend(sources_dict[key])

        # remove duplicate urls
        sources_list = list(dict.fromkeys(sources_list))

        # remove urls that aren't active or aren't real
        sources_list = [url for url in sources_list if validators.url(url)]

        nx.set_node_attributes(
            self.G,
            {target_node: sources_list},
            "causal sources",
        )
    
    def get_graph(self):
        return self.G