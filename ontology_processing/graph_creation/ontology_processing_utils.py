import networkx as nx
from networkx.readwrite import json_graph
import os

def get_source_types():
    return [
        "dc_source",
        "schema_academicBook",
        "schema_academicSourceNoPaywall",
        "schema_academicSourceWithPaywall",
        "schema_governmentSource",
        "schema_mediaSource",
        "schema_mediaSourceForConservatives",
        "schema_organizationSource",
    ]

def solution_sources(node):
    """Returns a flattened list of custom solution source values from each node key that matches
    custom_source_types string.
    node - NetworkX node
    source_types - list of sources types
    """
    source_types = get_source_types()
    # loop over each solution source key and append each returned value to the solution_sources list
    solution_source_list = list()
    for source_type in source_types:
        if "properties" in node and source_type in node["properties"]:
            solution_source_list.extend(node["properties"][source_type])

    solution_source_list = list(OrderedDict.fromkeys(solution_source_list))

    return solution_source_list

def get_valid_test_ont():
    return {
        "test ontology",
        "personal value",
        "achievement",
        "benevolence",
        "benevolence caring",
        "benevolence dependability",
        "conformity",
        "conformity interpersonal",
        "conformity rules",
        "face",
        "hedonism",
        "humility",
        "power",
        "power dominance",
        "power resources",
        "security",
        "security personal",
        "security societal",
        "self-direction",
        "self-direction autonomy of action",
        "self-direction autonomy of thought",
        "stimulation",
        "tradition",
        "universalism",
        "universalism concern",
        "universalism nature",
        "universalism tolerance",
    }


def get_non_test_ont():
    return {
        "value uncategorized (to do)",
        "risk solution",
        "adaptation",
        "geoengineering",
        "indirect adaptation",
        "indirect geoengineering",
        "indirect mitigration",
        "carbon pricing",
        "carbon tax",
        "emissions trading",
        "mitigation",
        "solution to indirect adaptation barrier",
        "solution to indirect mitigation barrier",
        "solution uncategorized (to do)",
    }


def remove_non_test_nodes(T, node, valid_test_ont, not_test_ont):
    if node in T.nodes:
        is_test_ont = False
        for c in T.nodes[node]["direct classes"]:
            if c in valid_test_ont:
                is_test_ont = True
            if c in not_test_ont:
                is_test_ont = False
                break
        if not is_test_ont:
            T.remove_node(node)
        else:
            is_test_ont = False


def get_test_ontology(T, valid_test_ont, not_test_ont):
    for edge in list(T.edges):
        node_a = edge[0]
        node_b = edge[1]
        remove_non_test_nodes(T, node_a, valid_test_ont, not_test_ont)
        remove_non_test_nodes(T, node_b, valid_test_ont, not_test_ont)


def give_alias(property_object):
    label_name = property_object.label[0]
    label_name = label_name.replace("/", "_or_")
    label_name = label_name.replace(" ", "_")
    label_name = label_name.replace(":", "_")
    property_object.python_name = label_name
    return label_name


def _save_graph_helper(G, outfile_path, fname="Climate_Mind_DiGraph", ext=".gpickle"):
    writer = {
        ".gpickle": nx.write_gpickle,
        ".gexf": nx.write_gexf,
        ".gml": nx.write_gml,
        ".graphml": nx.write_graphml,
        ".yaml": nx.write_yaml,
        ".json": lambda g, f: f.write(json_graph.jit_data(g, indent=4)),
    }
    mode = "wb"
    if ext in (".json", ".yaml"):
        mode = "w"
    file_path = os.path.join(outfile_path, fname + ext)
    with open(file_path, mode) as outfile:
        writer[ext](G, outfile)


def save_graph_to_pickle(G, outfile_path, fname="Climate_Mind_DiGraph"):
    _save_graph_helper(G, outfile_path, fname, ext=".gpickle")


def save_graph_to_gexf(G, outfile_path, fname="Climate_Mind_DiGraph"):
    _save_graph_helper(G, outfile_path, fname, ext=".gexf")


def save_graph_to_gml(G, outfile_path, fname="Climate_Mind_DiGraph"):
    _save_graph_helper(G, outfile_path, fname, ext=".gml")


def save_graph_to_graphml(G, outfile_path, fname="Climate_Mind_DiGraph"):
    _save_graph_helper(G, outfile_path, fname, ext=".graphml")


def save_graph_to_yaml(G, outfile_path, fname="Climate_Mind_DiGraph"):
    _save_graph_helper(G, outfile_path, fname, ext=".yaml")


def save_graph_to_json(G, outfile_path, fname="Climate_Mind_DiGraph"):
    _save_graph_helper(G, outfile_path, fname, ext=".json")


def save_test_ontology_to_json(G, outfile_path, fname="Climate_Mind_Digraph_Test_Ont"):
    save_graph_to_json(G, outfile_path, fname)
