import dash
import networkx as nx
import dash_html_components as html
import dash_core_components as dcc
import pickle
import textwrap


def draw_graph(name, G):
    N = nx.nx_agraph.to_agraph(G)
    N.edge_attr.update(directed=True)
    N = N.unflatten(f'-f -l6')
    N.layout(prog='dot', args='-Gratio=compress -Grankdir=TB -Gnodesep=0.5 -Gfontsize=20')
    N.draw(f"pictures/{name}.png", "png")

    # When exporting to JS somehow renders it vertically flipped. So we flip it back.
    N.layout(prog='dot', args='-Gratio=compress -Grankdir=BT -Gfontsize=25')

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


# Have to run makegraph function first to get the pickle!
with open("graphs_for_visualization.pickle", "rb") as f:
    preprocessed_data = pickle.load(f)




def convert_graph_to_cyto(G, tree_root):
    for node in G.nodes:
        node_label = G.nodes[node]['label']
        wrapped = textwrap.wrap(node_label, 20)

        G.nodes[node]['label'] = "\n".join(wrapped)
        G.nodes[node]['cyto_width'] = f'{len(max(wrapped, key=len)) / 1.5 + 3.5:.2f}em'
        G.nodes[node]['cyto_height'] = "{}em".format(len(wrapped) + 3)

    N = draw_graph(tree_root, G)

    total_cyto_data = nx.readwrite.json_graph.cytoscape_data(G)['elements']
    cyto_nodes = total_cyto_data['nodes']
    cyto_edges = total_cyto_data['edges']

    for edge in cyto_edges:
        edge['classes'] = []
        if 'risk solution' in G.nodes[edge['data']['source']] or 'risk solution' in G.nodes[
            edge['data']['target']]:
            edge['classes'].append('solution-edge')
        elif not edge['data']['properties']:
            # Edge is not connecting to risk solution! Check if it has sources.
            edge['classes'].append('edge-no-source')
            # print(edge, 'no source')

    # Extract x y positions using graphviz dot algo. Use x,y positions to make cytoscape graph
    for node in cyto_nodes:
        graphviz_node = N.get_node(node['data']['id'])
        position = graphviz_node.attr.get('pos', []).split(',')
        node['position'] = {'x': int(float(position[0])), 'y': int(float(position[1]))}

        if node['data']['id'] == tree_root:
            node['classes'] = 'tree_root'

        if 'risk solution' in node['data']:
            node['classes'] = 'risk-solution'

        if any(node['data']['personal_values_10']):
            node['classes'] = 'personal-value'

    return list(cyto_nodes) + list(cyto_edges)


total_cyto_data = {}

for graph in preprocessed_data:
    total_cyto_data[graph] = convert_graph_to_cyto(preprocessed_data[graph], graph)

# Stores the cytograph data so JS code can read it and render it.
# This data represents all graph data
cyto_storage = dcc.Store(
    id='cyto-storage',
    storage_type='memory',
    data=total_cyto_data
)
app.layout = html.Div([
    cyto_storage,
    html.Div(
        [
            html.Div(
                [
                    html.Div([
                        dcc.Dropdown(
                            id='select',
                            className='dropdowns',
                            options=[
                                {'label': name, 'value': name} for name in total_cyto_data.keys()
                            ],
                            value="downstream",
                            placeholder="graph type"
                        ), dcc.Dropdown(
                            id='search-nodes',
                            className='dropdowns',
                            placeholder="Search for nodes"
                        )], id="dropdowns-div"),
                    html.Div(id='cyto-graph-container')]
                , id="graph"),
            html.Div(id="right_controls", children=[
                dcc.Dropdown(
                    id="filter-type",
                    options=[
                        {'label': 'Personal value nodes/solutions without long descriptions', 'value': 'no_long_desc'},
                        {'label': 'Personal value nodes/edges without sources', 'value': 'no_sources'},
                        {'label': 'All personal values', 'value': 'personal_values'},
                        {'label': 'None', 'value': 'none'}
                    ],
                    placeholder="Choose filter"
                )
            ])]
        , id="upper_box"),
    html.Div(id='output', style={'whiteSpace': 'pre-wrap'}),
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

app.clientside_callback(
    dash.dependencies.ClientsideFunction(
        namespace='clientside',
        function_name='update_filter'
    ),
    dash.dependencies.Output('dummy4', 'children'),
    dash.dependencies.Input('filter-type', 'value')
)

# Updates the personal values in the dropdown.
app.clientside_callback(
    dash.dependencies.ClientsideFunction(
        namespace='clientside',
        function_name='update_personal_value'
    ),
    dash.dependencies.Output('dummy3', 'children'),
    [dash.dependencies.Input('select', 'value')],
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
    [dash.dependencies.Input('search-nodes', 'value')],
)


@app.callback(
    dash.dependencies.Output('search-nodes', 'options'),
    dash.dependencies.Input('select', 'value')
)
def test(input_value):
    if input_value in preprocessed_data:
        nodes = sorted(preprocessed_data[input_value].nodes())
    elif input_value in preprocessed_data['personal_value_slns']:
        nodes = sorted(preprocessed_data['personal_value_slns'][input_value])
    else:
        print("Invalid input value ", input_value)
    return [{'label': node, 'value': node} for node in nodes]


app.run_server(debug=True)
