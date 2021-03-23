import pickle
import textwrap
import os
import dash
import dash_core_components as dcc
import dash_html_components as html
import networkx as nx


def draw_graph(name, graph, output_png=False):
    """
    Converts an nx.DiGraph into a graphviz agraph. Lets us use layouting/positioning abilities of graphviz.
    Parameters
    ----------
    name - output file name
    G - nx.DiGraph to convert
    output_png - whether to write a PNG or not

    Returns
    -------
    Graphviz Agraph
    """
    N = nx.nx_agraph.to_agraph(graph)
    N.edge_attr.update(directed=True)
    N = N.unflatten(f'-f -l6')

    if output_png:
        N.layout(prog='dot', args='-Gratio=compress -Grankdir=TB -Gnodesep=0.5 -Gfontsize=20')
        N.draw(f"pictures/{name}.png", "png")

    # When exporting to JS somehow renders it vertically flipped. So we flip it back.
    N.layout(prog='dot', args='-Gratio=compress -Grankdir=BT -Gfontsize=25 -Granksep=1 -Gnodesep=1')

    return N


app = dash.Dash(__name__,
                external_scripts=[{'src': 'assets/make_cyto_graph.mjs', 'type': 'module'}],
                assets_ignore='.*mjs')

# TODO: update variable naming documentation to match pickle
# Cyto_data_(no)slns: list of elements that cytoscape.js receives. Contains all info needed to render the graph.
# edge_data: adjacency dict. Created by edges_to_dict function.
# graph_data_(no)sln: dict of nx.DiGraph keyed by personal value. Currently unused.
#       Access by edge_data[personal value string][edge1][edge2] = edge properties (also a dict)
#       Contains all nodes, including solutions.
# These two below are currently unused as cytoscape.js graph functions handle everything already.
# We barely do any calculations in Python.
# cyto_data_noslns, graph_data_noslns = compute_graphs(G_noslns)
# edge_data = {personal_value: edges_to_dict(graph) for personal_value, graph in graph_data_slns.items()}
# Cache in set so we avoid computation

if not os.path.exists("graphs_for_visualization.pickle"):
    from ontology_processing.graph_creation.make_graph import makeGraph

    makeGraph('Bx50aIKwEALYNmYl0CFzNp.owl', 'output.csv')

# Have to run makegraph function first to get the pickle!
with open("graphs_for_visualization.pickle", "rb") as f:
    preprocessed_data = pickle.load(f)


def convert_graph_to_cyto(G, tree_root=None):
    """
    Converts nx.DiGraph into a cytoscape-compatible elements list.
    Sample elements list:

        {'data': {'id': 'one', 'label': 'Node 1'}, 'position': {'x': 50, 'y': 50}, 'classes': ['risk-solution']}, # node
        {'data': {'id': 'two', 'label': 'Node 2'}, 'position': {'x': 200, 'y': 200}},                             # node
        {'data': {'source': 'one', 'target': 'two', 'label': 'Node 1 to 2'}}                                      # edge
    Parameters
    ----------
    G - nx.DiGraph
    tree_root - optional parameter to highlight tree root (e.g. personal value) a special color.

    Returns
    -------
    List compatible with cytoscape.js
    """
    # Use graphviz to layout the graph for us
    N = nx.nx_agraph.to_agraph(G)
    N.edge_attr.update(directed=True)
    N = N.unflatten('-f -l6')
    N.layout(prog='dot', args='-Gratio=compress -Grankdir=BT -Gfontsize=25')

    for node in G.nodes:
        node_label = G.nodes[node]['label']
        wrapped = textwrap.wrap(node_label, 20)

        G.nodes[node]['label'] = "\n".join(wrapped)
        G.nodes[node]['__cyto_width'] = f'{len(max(wrapped, key=len)) / 1.5 + 3.5:.2f}em'
        G.nodes[node]['__cyto_height'] = "{}em".format(len(wrapped) + 3)

    N = draw_graph(tree_root, G)

    total_cyto_data = nx.readwrite.json_graph.cytoscape_data(G)['elements']
    cyto_nodes = total_cyto_data['nodes']
    cyto_edges = total_cyto_data['edges']

    for edge in cyto_edges:
        edge['classes'] = G[edge['data']['source']][edge['data']['target']]['cyto_classes']

    # Extract x y positions using graphviz dot algo. Use x,y positions to make cytoscape graph
    # Also doing some preprocessing
    for node in cyto_nodes:
        graphviz_node = N.get_node(node['data']['id'])
        position = graphviz_node.attr.get('pos', []).split(',')
        node['classes'] = G.nodes[node['data']['id']]['cyto_classes']
        node['position'] = {'x': int(float(position[0])), 'y': int(float(position[1]))}

    return list(cyto_nodes) + list(cyto_edges)


total_cyto_data = {}
if os.environ['DEBUG_USE_CACHE']:
    with open('processed_cyto_data.pickle', 'rb') as f:
        total_cyto_data = pickle.load(f)
else:
    print("Recreating cyto data")
    for graph in preprocessed_data:
        total_cyto_data[graph] = convert_graph_to_cyto(preprocessed_data[graph], graph)
    with open('processed_cyto_data.pickle', 'wb') as f:
        pickle.dump(total_cyto_data, f)

# Stores the cytograph data so JS code can read it and render it.
# This data represents all graph data
cyto_storage = dcc.Store(
    id='cyto-storage',
    storage_type='memory',
    data=total_cyto_data
)

layout_parts = {
    'graph-select': dcc.Dropdown(
        id='graph-select',
        className='dropdowns',
        options=[
            {'label': name, 'value': name} for name in total_cyto_data.keys()
        ],
        value="downstream",
        placeholder="graph type"
    ),
    'node-search': dcc.Dropdown(
        id='node-search',
        className='dropdowns',
        placeholder="Search for nodes"
    ),
    'right-controls': html.Div(id="right-controls"),
    'cytoscape-graph-container': html.Div(id="cytoscape-graph-container"),
    'bottom-controls': html.Div(id='bottom-controls')
}

app.layout = html.Div([
    cyto_storage,
    html.Div(children=list(layout_parts.values()), className='grid-container'),
    html.Div(id='dummy1'), html.Div(id='dummy2'), html.Div(id='dummy3'), html.Div(id='dummy4'), html.Div(id='dummy5')
])

# Runs on load to fill html.Div element output with custom HTMl tags
# Not using Dash HTML library because much more complicated than writing plain HTML.
app.clientside_callback(
    dash.dependencies.ClientsideFunction(
        # Function is located in file assets/callbc.js
        namespace='clientside',
        function_name='fill_output_div'
    ),
    dash.dependencies.Output('dummy2', 'children'),
    dash.dependencies.Input('dummy1', 'children')
)

# Updates the personal values in the dropdown.
app.clientside_callback(
    dash.dependencies.ClientsideFunction(
        namespace='clientside',
        function_name='update_personal_value'
    ),
    dash.dependencies.Output('dummy3', 'children'),
    [dash.dependencies.Input('graph-select', 'value')],
)

# Copies our Python cytoscape_data to Javascript.
# This contains all the data needed to render all graphs.
app.clientside_callback(
    dash.dependencies.ClientsideFunction(
        namespace='clientside',
        function_name='update_storage_globals'
    ),
    dash.dependencies.Output('dummy1', 'children'),
    [dash.dependencies.Input('cyto-storage', 'data')],
)

# Copies our Python cytoscape_data to Javascript.
# This contains all the data needed to render all graphs.
app.clientside_callback(
    dash.dependencies.ClientsideFunction(
        namespace='clientside',
        function_name='search_nodes'
    ),
    dash.dependencies.Output('dummy5', 'children'),
    [dash.dependencies.Input('node-search', 'value')],
)


@app.callback(
    dash.dependencies.Output('node-search', 'options'),
    dash.dependencies.Input('graph-select', 'value')
)
def test(input_value):
    if input_value in preprocessed_data:
        nodes = sorted(preprocessed_data[input_value].nodes())
    elif input_value in preprocessed_data['personal_value_slns']:
        nodes = sorted(preprocessed_data['personal_value_slns'][input_value])
    else:
        print("Invalid input value ", input_value)
        return
    return [{'label': node, 'value': node} for node in nodes]


app.run_server(debug=True)
