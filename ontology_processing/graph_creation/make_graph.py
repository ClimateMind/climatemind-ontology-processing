import pickle
import argparse
import networkx as nx
import pandas as pd
import validators

import owlready2
from owlready2 import sync_reasoner
from collections import OrderedDict

from ontology_processing.graph_creation.ontology_processing_utils import (
    give_alias,
    save_test_ontology_to_json,
    save_graph_to_pickle,
    get_valid_test_ont,
    get_non_test_ont,
    remove_non_test_nodes,
    get_test_ontology,
)
from ontology_processing.graph_creation.process_visualization import ProcessVisualization
from ontology_processing.graph_creation.process_myths import ProcessMyths
from ontology_processing.graph_creation.process_causal_sources import ProcessCausalSources
from ontology_processing.graph_creation.make_graph_class import MakeGraph

# Set a lower JVM memory limit
owlready2.reasoning.JAVA_MEMORY = 500

def make_graph(onto_path, edge_path, output_folder_path):
    mg = MakeGraph(onto_path, edge_path, output_folder_path)
    mg.load_ontology()
    mg.set_properties()
    mg.automate_reasoning()
    mg.add_edges_to_graph()
    mg.build_attributes_dict()
    to_remove = mg.set_edge_properties()
    mg.remove_edge_properties_from_nodes(to_remove)
    mg.make_acyclic()
    mitigation_solutions, nodes_upstream_greenhouse_effect = mg.get_mitigations()
    mg.add_mitigations(mitigation_solutions)
    total_adaptation_nodes = mg.process_node_identity()
    G = mg.get_graph()

    annotated_graph = mg.get_annotated()
    pv = ProcessVisualization(annotated_graph)
    pv.annotate_graph_with_problems()
    pv.get_subgraphs(total_adaptation_nodes, mitigation_solutions)
    pv.save_output(output_folder_path)

    pm = ProcessMyths(G)
    subgraph_downstream_adaptations = pv.get_downstream_adaptations()
    pm.process_myths(subgraph_downstream_adaptations, nodes_upstream_greenhouse_effect)
    pm.add_general_myths()
    G = pm.get_graph()

    cs = ProcessCausalSources(G)
    cs.process_sources()
    G = cs.get_graph()

    save_graph_to_pickle(G, output_folder_path)

    T = G.copy()

    valid_test_ont = get_valid_test_ont()
    not_test_ont = get_non_test_ont()
    get_test_ontology(T, valid_test_ont, not_test_ont)

    save_test_ontology_to_json(T, output_folder_path)