import networkx as nx
import dash
import dash_cytoscape as cyto
import dash_html_components as html
import dash_core_components as dcc
from ontology_processing.graph_creation.make_graph import make_acyclic

import textwrap

G1 = nx.read_gpickle('Climate_Mind_DiGraph.gpickle')
G1 = make_acyclic(G1)


# Filter functions to pass onto subgraph_view. Filters out any nodes we don't want (myth/solution)
def filter_node(input_node):
    return 'risk solution' not in G1.nodes[input_node] and 'myth' not in G1.nodes[input_node]


# Only want causal edges in our graph
def filter_edge(e1, e2):
    return G1[e1][e2]['type'] == 'causes_or_promotes'


G = nx.subgraph_view(G1, filter_node=filter_node, filter_edge=filter_edge)

# Holds the complete graph cytoscape data (node positions + labels) for each node with a personal value associated
value_nodes = {node_tuple[0]: list() for node_tuple in G.nodes.data('personal_values_10', [None]) if
               any(node_tuple[1])}

for value_key, cyto_elements in value_nodes.items():
    subtree = nx.DiGraph()
    for edge in nx.edge_bfs(G, value_key, 'reverse'):
        subtree.add_edge(edge[0], edge[1], **G[edge[0]][edge[1]])

    nodes_to_remove = set()
    for node in subtree.nodes:
        nx.set_node_attributes(subtree, {node: G.nodes[node]})
        # Debug checks
        # if subtree.nodes[node].get('test ontology', None) != ['test ontology']:
        #     raise RuntimeError("test ontology present in graph")

        # Manual wrap text so graph is more condensed.
        if len(subtree.nodes[node]['label']) > 20:
            subtree.nodes[node]['label'] = textwrap.fill(subtree.nodes[node]['label'], 20)

    N = nx.nx_agraph.to_agraph(subtree)

    N.edge_attr.update(directed=True)
    N.layout(prog='dot', args='-Gratio=compress -Gsize="30, 30" -Grankdir=BT -Gnodesep=0.01 -Nmargin="0.01,0.01"')
    N.draw(f"{value_key}.png", "png")
    # N.write(f"{value_key}.dot")

    total_cyto_data = nx.readwrite.json_graph.cytoscape_data(subtree)['elements']
    cyto_nodes = total_cyto_data['nodes']
    cyto_edges = total_cyto_data['edges']

    # Extract x y positions using graphviz dot algo. Use x,y positions to make cytoscape graph
    for node in cyto_nodes:
        graphviz_node = N.get_node(node['data']['id'])
        position = graphviz_node.attr.get('pos', []).split(',')
        node['data'] = {**G.nodes[node['data']['id']], 'id': node['data']['id']}
        node['position'] = {'x': int(float(position[0])), 'y': int(float(position[1]))}

        if node['data']['id'] == value_key:
            node['classes'] = 'tree_root'

    cyto_elements[:] = list(cyto_nodes) + list(cyto_edges)

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Dropdown(
        id='select',
        options=[
            {'label': name, 'value': name} for name in value_nodes.keys()
        ],
        style={'width': '70%'}

    ),
    cyto.Cytoscape(
        id='cytoscape-two-nodes',
        layout={'name': 'preset'},
        style={'width': '70%', 'height': '800px'},
        elements=[],
        stylesheet=[
            {
                'selector': "edge",
                'style': {
                    'width': 3,
                    'line-color': '#ccc',
                    'target-arrow-color': 'red',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'arrow-scale': 2
                }
            }, {
                'selector': 'node',
                'style': {
                    'label': 'data(label)',
                    'text-wrap': 'wrap',
                    'text-max-width': '10em',
                    'width': '1em',
                    'height': '1em'
                }
            }, {
                'selector': '.tree_root',
                'style': {
                    'background-color': 'blue'
                }
            }
        ]
    )
])


@app.callback(
    dash.dependencies.Output('cytoscape-two-nodes', 'elements'),
    [dash.dependencies.Input('select', 'value')]
)
def change_viewed_key(new_key):
    if new_key is None:
        new_key = next(iter(value_nodes))
    print(f"changing to: {new_key}")
    return value_nodes[new_key]


app.run_server(debug=True)
