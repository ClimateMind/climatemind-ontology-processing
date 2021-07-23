import networkx as nx
from collections import OrderedDict

from ontology_processing.graph_creation.ontology_processing_utils import (
    get_source_types,
)

class ProcessMyths:
    """
    Climate Myths are shown to the end user. Some myths are attached to a climate
    solution and others are common myths not attached to a solution. Both need to
    be added to the NetworkX object for use by the API.
    """
    def __init__(self, G):
        self.G = G
        self.source_types = get_source_types()
        self.general_myths = None
    
    def process_myths(self, subgraph_downstream_adaptations, nodes_upstream_greenhouse_effect):
        """
        Structures myth data in NetworkX object to be easier for API use.
        """
        general_myths = list()
        all_myths = list(nx.get_node_attributes(self.G, "myth").keys())

        for myth in all_myths:
            node_neighbors = self.G.neighbors(myth)
            for neighbor in node_neighbors:
                if self.G[myth][neighbor]["type"] == "is_a_myth_about":

                    impact_myths = []

                    if "risk solution" in self.G.nodes[neighbor].keys():
                        if "solution myths" not in self.G.nodes[neighbor].keys():
                            solution_myths = []
                        else:
                            solution_myths = self.G.nodes[neighbor]["solution myths"]
                        solution_myths.append(myth)
                        nx.set_node_attributes(
                            self.G, {neighbor: solution_myths}, "solution myths"
                        )
                    if subgraph_downstream_adaptations.has_node(neighbor):
                        if "impact myths" not in self.G.nodes[neighbor].keys():
                            impact_myths = []
                        else:
                            impact_myths = self.G.nodes[neighbor]["impact myths"]
                        impact_myths.append(myth)
                        nx.set_node_attributes(self.G, {neighbor: impact_myths}, "impact myths")
                    if neighbor in nodes_upstream_greenhouse_effect:
                        general_myths.append(myth)
            self.add_myth_sources(myth)

        # get unique general myths
        self.general_myths = list(dict.fromkeys(general_myths))

        self.sort_myths()

    def add_myth_sources(self, myth):
        """
        Process myth sources into nice field called 'myth sources' 
        with only unique urls from any source type
        """
        myth_sources = list()
        for source_type in self.source_types:
            if (
                "properties" in self.G.nodes[myth]
                and source_type in self.G.nodes[myth]["properties"]
            ):
                myth_sources.extend(self.G.nodes[myth]["properties"][source_type])

        myth_sources = list(
            OrderedDict.fromkeys(myth_sources)
        )  # removes any duplicates while preserving order
        nx.set_node_attributes(
            self.G,
            {myth: myth_sources},
            "myth sources",
        )

    def sort_myths(self):
        """
        Sort the myths by popularity (skeptical science)
        """
        general_myths_dict = dict()

        for myth in self.general_myths:
            general_myths_dict[myth] = self.G.nodes[myth]["data_properties"]["myth_frequency"]

        general_myths_sorted = sorted(
            general_myths_dict,
            key=general_myths_dict.get,
            reverse=True,
        )

        self.general_myths = general_myths_sorted
    
    def add_general_myths(self):
        """
        Update the networkx object to have a 'general myths' field and 
        include in it all nodes from mitigation_solutions
        """
        nx.set_node_attributes(
            self.G,
            {"increase in greenhouse effect": self.general_myths},
            "general myths",
        )
    
    def get_graph(self):
        return self.G