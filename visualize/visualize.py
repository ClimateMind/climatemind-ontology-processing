import networkx as nx
import dash
import dash_cytoscape as cyto
import dash_html_components as html
import dash_core_components as dcc
from ontology_processing.graph_creation.make_graph import make_acyclic
from collections import deque
import textwrap

G1 = nx.read_gpickle('visualize/Climate_Mind_DiGraph.gpickle')
G1 = make_acyclic(G1)


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

            # Manual wrap text so graph is more condensed.
            if len(subtree.nodes[node]['label']) > 20:
                subtree.nodes[node]['label'] = textwrap.fill(subtree.nodes[node]['label'], 20)

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
        # N.layout(prog='dot', args='-Gratio=compress -Gsize="30, 30" -Grankdir=BT -Gnodesep=0.01 -Nmargin="0.01,0.01"')
        N.layout(prog='dot')
        N.draw(f"{value_key}.png", "png")
        N.write(f"{value_key}.dot")

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
            node['data'] = {**G.nodes[node['data']['id']], 'id': node['data']['id']}
            node['position'] = {'x': int(float(position[0])), 'y': int(float(position[1]))}

            if node['data']['id'] == value_key:
                node['classes'] = 'tree_root'

            if 'risk solution' in node['data']:
                node['classes'] = 'risk-solution'

            if 'myth' in node['data']:
                node['classes'] = 'myth'

        cyto_elements[:] = list(cyto_nodes) + list(cyto_edges)
    return cyto_data, graph_data


cyto_data_noslns, graph_data_noslns = compute_graphs(G_noslns)
cyto_data_slns, graph_data_slns = compute_graphs(G_sln)
app = dash.Dash(__name__)

node_storage = dcc.Store(
    id='node-storage',
    storage_type='local',
    data=dict(G_noslns.nodes(data=True))
)

# To be filled when in a callback
edge_storage = dcc.Store(
    id='edge-storage',
    storage_type='local'
)
app.layout = html.Div([
    node_storage,
    edge_storage,

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
            )], id="graph-controls"),
    cyto.Cytoscape(
        id='cytoscape-two-nodes',
        layout={'name': 'preset'},
        style={'height': '800px'},
        elements=[],
        stylesheet=[

            {
                'selector': "edge",
                'style': {
                    'width': 1,
                    'line-color': '#ccc',
                    'target-arrow-color': 'red',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'arrow-scale': 2,
                    'line-opacity': 0.9
                }
            }, {
                'selector': 'node',
                'style': {
                    'label': 'data(label)',
                    'text-wrap': 'wrap',
                    'text-max-width': '12em',
                    'text-halign': 'center',
                    'text-valign': 'center',
                    'width': 'label',
                    'height': 'label',
                    'font-size': 20,
                    'shape': 'round-rectangle',
                    'background-color': 'orange'
                }
            }, {
                'selector': 'node',
                'style': {
                    'padding': '10px',
                }
            }, {
                'selector': '.tree_root',
                'style': {
                    'background-color': 'blue'
                }
            }, {
                'selector': '.risk-solution',
                'style': {
                    'background-color': 'green'
                }
            }, {
                'selector': '.solution-edge',
                'style': {
                    'line-color': 'green',
                    'line-opacity': 0.3
                }
            }
        ]
    ),
    html.Div(id='output', style={'whiteSpace': 'pre-wrap'}),
    html.Div(id='dummy'), html.Div(id='dummy1')
])


@app.callback(
    [dash.dependencies.Output('cytoscape-two-nodes', 'elements'), dash.dependencies.Output('edge-storage', 'data')],
    [dash.dependencies.Input('select', 'value'), dash.dependencies.Input('solutions-check', 'value')]
)
def change_viewed_key(new_key, view_slns):
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

    if new_key is None:
        new_key = next(iter(cyto_data_slns))

    print(f"changing to: {new_key}", view_slns)

    if view_slns:
        return cyto_data_slns[new_key], edges_to_dict(graph_data_slns[new_key])
    else:
        return cyto_data_noslns[new_key], edges_to_dict(graph_data_noslns[new_key])


app.clientside_callback(
    dash.dependencies.ClientsideFunction(
        namespace='clientside',
        function_name='mouse_over_func'
    ),
    dash.dependencies.Output('dummy1', 'children'),
    dash.dependencies.Input('cytoscape-two-nodes', 'mouseoverNodeData'),
    dash.dependencies.State('edge-storage', 'data')
)

app.clientside_callback(
    dash.dependencies.ClientsideFunction(
        namespace='clientside',
        function_name='fill_output_div'
    ),
    dash.dependencies.Output('dummy', 'children'),
    dash.dependencies.Input('dummy', 'id')
)

app.run_server(debug=True)
