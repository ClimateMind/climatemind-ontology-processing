import validators
import networkx as nx

from ontology_processing.graph_creation.ontology_processing_utils import (
    get_source_types,
)

class ProcessCausalSources:
    """
    Causal sources are sources that belong to the cause_effect edge relation. 
    They aren’t sources that prove existence of a node. 
    They are sources that prove existence of the cause_effect relationship between 2 nodes. 
    These sources are identified in the OWL ontology when they are the same source curated 
    on 2 neighboring nodes that are also connected by the cause_effect relation.
    """
    def __init__(self, G):
        self.G = G
        self.source_types = get_source_types()
        self.causal_sources = None
    
    def process_sources(self):
        """
        Get causal sources from each node
        """
        for target_node in self.G.nodes:
            self.get_causal_relationships(target_node)

            if self.causal_sources:
                self.collapse_url(target_node)

    def get_causal_relationships(self, target_node):
        """
        Get list nodes that have a relationship with the target node (are neighbor nodes), 
        then filter it down to just the nodes with the causal relationship with the target node
        """
        self.causal_sources = []
        predecessor_nodes = self.G.predecessors(target_node)
        for predecessor_node in predecessor_nodes:
            if self.G[predecessor_node][target_node]["type"] == "causes_or_promotes":
                if self.G[predecessor_node][target_node]["properties"]:
                    self.causal_sources.append(
                        self.G[predecessor_node][target_node]["properties"]
                    )

    def collapse_url(self, target_node):
        """
        Collapse down to just list of unique urls. Strips off the type of source
        and the edge it originates from
        """
        sources_list = []

        for sources_dict in self.causal_sources:
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