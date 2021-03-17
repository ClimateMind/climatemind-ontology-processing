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

    do_bfs(start_node)

    while queue:
        do_bfs(queue.pop())

    for node in new_graph.nodes:
        nx.set_node_attributes(new_graph, {node: graph.nodes[node]})

    return new_graph


# Filter functions to pass onto subgraph_view. Filters out any nodes we don't want (myth/solution)
def filter_node(input_node):
    return 'myth' not in G1.nodes[input_node]


# Only want causal edges in our graph
def filter_edge(e1, e2):
    return True
    return G1[e1][e2]['type'] == 'causes_or_promotes'


G = nx.subgraph_view(G1, filter_node=filter_node, filter_edge=filter_edge)
# G = custom_bfs(G, 'increase in physical violence')
# N = nx.nx_agraph.to_agraph(G)


# Holds the complete graph cytoscape data (node positions + labels) for each node with a personal value associated
value_nodes = {node_tuple[0]: list() for node_tuple in G.nodes.data('personal_values_10', [None]) if
               any(node_tuple[1])}

value_nodes = {'increase in physical violence': value_nodes['increase in physical violence']}

for value_key, cyto_elements in value_nodes.items():
    # subtree = nx.DiGraph()
    # for e1, e2, direction in nx.edge_bfs(G, value_key, 'ignore'):
    #     if direction == 'reverse':
    #         subtree.add_edge(e1, e2, **G[e1][e2])
    #     elif direction == 'forward':
    #         if 'risk solution' in G.nodes[e2] or True:
    #             subtree.add_edge(e1, e2, **G[e1][e2])

    subtree = custom_bfs(G, value_key)
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
    N = N.unflatten(f'-f -l15')
    N.layout(prog='dot', args='-Gratio=compress -Gsize="30, 30" -Grankdir=BT -Gnodesep=0.01 -Nmargin="0.01,0.01"')
    # N.draw(f"{value_key}.png", "png")
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

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Dropdown(
        id='select',
        options=[
            {'label': name, 'value': name} for name in value_nodes.keys()
        ],
        style={'display': 'inline-block', 'width': '70%'}
    ),
    dcc.Checklist(
        id='solutions-check',
        options=[
            {'label': 'See solutions', 'value': 'solution'}
        ],
        style={
            'display': 'inline-block'
        }
    ),
    cyto.Cytoscape(
        id='cytoscape-two-nodes',
        layout={'name': 'preset'},
        style={'width': '70%', 'height': '800px'},
        elements=[],
        stylesheet=[
            {
                'selector': '.tree_root',
                'style': {
                    'background-color': 'blue',
                    'width': '50',
                    'height': '50'
                }
            },
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
                    'text-max-width': '10em'
                }
            }, {
                'selector': '.risk-solution',
                'style': {
                    'background-color': 'green'
                }
            }, {
                'selector': '.solution-edge',
                'style': {
                    'line-color': 'green'
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


@app.callback(
    dash.dependencies.Output('cytoscape-two-nodes', 'stylesheet'),
    [dash.dependencies.Input('solutions-check', 'value')],
    [dash.dependencies.State('cytoscape-two-nodes', 'stylesheet')]
)
def toggle_solution_view(yes_solution, stylesheet):
    print('toggled')

    for style in stylesheet:
        if style['selector'] in ['.risk-solution', '.solution-edge']:
            style['style']['display'] = 'element' if yes_solution else 'none'

    return stylesheet


app.run_server(debug=True)
