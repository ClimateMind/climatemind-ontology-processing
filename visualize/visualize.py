import networkx as nx
import dash
import dash_cytoscape as cyto
import dash_html_components as html
import dash_core_components as dcc
from ontology_processing.graph_creation.make_graph import make_acyclic
from collections import deque
import textwrap

app = dash.Dash(__name__,
                external_scripts=[{'src': 'assets/make_cyto_graph.mjs', 'type': 'module'}],
                assets_ignore='.*\\.mjs')

G1 = nx.read_gpickle('visualize/Climate_Mind_DiGraph.gpickle')
G1 = make_acyclic(G1)

# Copy risk solution to risk-solution. Spaces make some trouble in JS.
for node in G1.nodes:
    if 'risk solution' in G1.nodes[node]:
        G1.nodes[node]['risk-solution'] = G1.nodes[node]['risk solution']


def custom_bfs(graph, start_node):
    queue = deque()
    new_graph = nx.DiGraph()

    def do_bfs(element):
        for in_edge in graph.in_edges(element, data=True):
            new_graph.add_edge(in_edge[0], in_edge[1], **in_edge[2])
            queue.append(in_edge[0])
        for out_edge in graph.out_edges(element, data=True):
            if 'risk solution' in graph.nodes[out_edge[1]]:
                new_graph.add_edge(out_edge[0], out_edge[1], **out_edge[2], weight=10)
                # We don't append to queue because don't want to explore further. solutions are terminal leaf nodes.

    do_bfs(start_node)

    while queue:
        do_bfs(queue.pop())

    for node in new_graph.nodes:
        nx.set_node_attributes(new_graph, {node: graph.nodes[node]})

    return new_graph


# Filter functions to pass onto subgraph_view. Filters out any nodes we don't want (myth/solution)
def filter_node(input_node):
    return 'myth' not in G1.nodes[input_node]


def filter_node_no_solutions(input_node):
    return filter_node(input_node) and 'risk solution' not in G1.nodes[input_node]


# Only want causal edges in our graph
def filter_edge(e1, e2):
    return True
    return G1[e1][e2]['type'] == 'causes_or_promotes'


G_sln = nx.subgraph_view(G1, filter_node=filter_node, filter_edge=filter_edge)
G_noslns = nx.subgraph_view(G1, filter_node=filter_node_no_solutions, filter_edge=filter_edge)


def compute_graphs(G):
    # Holds the complete graph cytoscape data (node positions + labels) for each node with a personal value associated
    cyto_data = {node_tuple[0]: list() for node_tuple in G.nodes.data('personal_values_10', [None]) if
                 any(node_tuple[1])}

    cyto_data = {'increase in physical violence': cyto_data['increase in physical violence']}

    graph_data = dict.fromkeys(cyto_data.keys())
    for value_key, cyto_elements in cyto_data.items():

        subtree = custom_bfs(G, value_key)
        for node in subtree.nodes:
            nx.set_node_attributes(subtree, {node: G.nodes[node]})

            subtree.nodes[node]['label'] = textwrap.fill(subtree.nodes[node]['label'], 20)
            subtree.nodes[node]['cyto_width'] = '12em'
            subtree.nodes[node]['cyto_height'] = "{}em".format(subtree.nodes[node]['label'].count('\n') + 1.4)

        graph_data[value_key] = subtree

        N = nx.nx_agraph.to_agraph(subtree)

        # Create graphviz subgraphs connecting solutions to their nodes.
        # Subgraphs help place solutions closer to their nodes
        for node in subtree.nodes:
            if 'risk' in subtree.nodes[node]:
                connected_solutions = [sln[1] for sln in subtree.out_edges(node, data=True) if
                                       'risk solution' in subtree.nodes[sln[1]]]
                connected_solutions.append(node)
                N.add_subgraph(connected_solutions, f"cluster_{node}")
        N.edge_attr.update(directed=True)
        N = N.unflatten(f'-f -l6')
        N.layout(prog='dot', args=' -Gsize="30, 30" -Grankdir=BT -Gnodesep=1.0')
        # N.draw(f"{value_key}.png", "png")
        # N.write(f"{value_key}.dot")

        total_cyto_data = nx.readwrite.json_graph.cytoscape_data(subtree)['elements']
        cyto_nodes = total_cyto_data['nodes']
        cyto_edges = total_cyto_data['edges']

        for edge in cyto_edges:
            if 'risk solution' in G.nodes[edge['data']['source']] or 'risk solution' in G.nodes[edge['data']['target']]:
                edge['classes'] = 'solution-edge'

        # Extract x y positions using graphviz dot algo. Use x,y positions to make cytoscape graph
        for node in cyto_nodes:
            graphviz_node = N.get_node(node['data']['id'])
            position = graphviz_node.attr.get('pos', []).split(',')
            node['position'] = {'x': int(float(position[0])), 'y': int(float(position[1]))}

            if node['data']['id'] == value_key:
                node['classes'] = 'tree_root'

            if 'risk solution' in node['data']:
                node['classes'] = 'risk-solution'

            if 'myth' in node['data']:
                node['classes'] = 'myth'

        cyto_elements[:] = list(cyto_nodes) + list(cyto_edges)
    return cyto_data, graph_data


def edges_to_dict(graph):
    edge_storage_data = {}
    for (e1, e2), edge_properties in dict(graph.out_edges).items():
        if e1 not in edge_storage_data:
            edge_storage_data[e1] = {}
        edge_storage_data[e1][e2] = {**edge_properties, 'direction': 'forward'}

    for (e1, e2), edge_properties in dict(graph.in_edges).items():
        if e2 not in edge_storage_data:
            edge_storage_data[e2] = {}
        edge_storage_data[e2][e1] = {**edge_properties, 'direction': 'reverse'}
    return edge_storage_data


# Cyto_data_(no)slns: list of elements that cytoscape.js receives. Contains all info needed to render the graph.
# graph_data_(no)sln: dict of nx.DiGraph keyed by personal value.
# edge_data: adjacency dict. Created by edges_to_dict function.
#       Access by edge_data[personal value string][edge1][edge2] = edge properties (also a dict)
#       Contains all nodes, including solutions.
# cyto_data_noslns, graph_data_noslns = compute_graphs(G_noslns)
cyto_data_slns, graph_data_slns = compute_graphs(G_sln)
# edge_data = {personal_value: edges_to_dict(graph) for personal_value, graph in graph_data_slns.items()}


# To be filled when in a callback
# TODO: implement cyto storage for no solutions case
cyto_storage = dcc.Store(
    id='cyto-storage',
    storage_type='memory',
    data=cyto_data_slns
)
app.layout = html.Div([
    cyto_storage,
    html.Div(
        [
            dcc.Dropdown(
                id='select',
                options=[
                    {'label': name, 'value': name} for name in cyto_data_slns.keys()
                ]
            ),
            dcc.Checklist(
                id='solutions-check',
                options=[
                    {'label': 'See solutions', 'value': 'solution'}
                ],
                value=["solution"]
            )]
        , id="graph-controls"),
    html.Div(id='cyto-graph-container'),
    html.Div(id='output', style={'whiteSpace': 'pre-wrap'}),
    html.Div(id='dummy1'), html.Div(id='dummy2'), html.Div(id='dummy3')
])

# Runs on load to fill html.Div element output with custom HTMl tags
# Not using Dash HTML library because much more complicated than writing plain HTML.
app.clientside_callback(
    dash.dependencies.ClientsideFunction(
        namespace='clientside',
        function_name='fill_output_div'
    ),
    dash.dependencies.Output('dummy2', 'children'),
    dash.dependencies.Input('dummy1', 'children')
)

# # User has selected a new personal value.
# # Updates clientside browser storage with new information about the new personal value.
# @app.callback(
#     [dash.dependencies.Output('cyto-storage', 'data'), dash.dependencies.Output('edge-storage', 'data')],
#     [dash.dependencies.Input('select', 'value'), dash.dependencies.Input('solutions-check', 'value')]
# )
# def change_viewed_key(new_key, view_slns):
#     # Dash calls all callbacks upon first load with None arguments.
#     if new_key is None:
#         new_key = next(iter(cyto_data_slns))
#
#     print(f"changing to: {new_key}", view_slns)
#
#     if view_slns:
#         updated_cyto_data = cyto_data_slns[new_key]
#     else:
#         updated_cyto_data = cyto_data_slns[new_key]
#
#     return updated_cyto_data, edge_data[new_key]


app.clientside_callback(
    dash.dependencies.ClientsideFunction(
        namespace='clientside',
        function_name='update_storage_globals'
    ),
    dash.dependencies.Output('dummy1', 'children'),
    [dash.dependencies.Input('cyto-storage', 'data')],
)

app.run_server(debug=True)
