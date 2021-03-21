import networkx as nx
import dash
import dash_cytoscape as cyto
import dash_html_components as html
import dash_core_components as dcc
from ontology_processing.graph_creation.make_graph import make_acyclic
from collections import deque
import textwrap

import pickle

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


# Have to run makegraph function first to get the pickle!
with open("graphs_for_visualization.pickle", "rb") as f:
    preprocessed_data = pickle.load(f)
    cyto_data_slns = dict(
        upstream_mitigations=preprocessed_data["cyto_upstream_mitigations"],
        downstream_adaptations=preprocessed_data["cyto_downstream_adaptations"],
        upstream=preprocessed_data["cyto_upstream"],
        downstream=preprocessed_data["cyto_downstream"],
        **preprocessed_data["cyto_downstream_adaptations_pv"],
        # personal_value=preprocessed_data["personal_value"]
    )

# Stores the cytograph data so JS code can read it and render it.
# This data represents all graph data
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
                ],
                value="downstream"
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
        function_name='update_personal_value'
    ),
    dash.dependencies.Output('dummy3', 'children'),
    [dash.dependencies.Input('select', 'value')],
)


# Copies our Python object to Javascript.
app.clientside_callback(
    dash.dependencies.ClientsideFunction(
        namespace='clientside',
        function_name='update_storage_globals'
    ),
    dash.dependencies.Output('dummy1', 'children'),
    [dash.dependencies.Input('cyto-storage', 'data')],
)

app.run_server(debug=True)
