console.log("loaded")
if (!window.dash_clientside) {
    window.dash_clientside = {};
}
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        mouse_over_func: function (node_data, edge_data) {
            // console.log(node_data, edge_data);
            console.log(edge_data[node_data['id']])
            //document.getElementById('output').innerHTML = Object.keys(edge_data[node_data['id']]).join('\n')
            // document.getElementById('outer_edges_output').innerText =  Object.keys().join('\n')

            all_edges = edge_data[node_data['id']]
            outer_edges = []
            inner_edges = []

            for( edge in all_edges ) {
                if(all_edges[edge].direction == "reverse") {
                    inner_edges.push(edge)
                } else {
                    outer_edges.push(edge)
                }
            }

            document.getElementById('outer_edges_output').innerText = outer_edges.join('.\n\n')
            document.getElementById('inner_edges_output').innerText = inner_edges.join('.\n\n')

        },
        fill_output_div: function (dummy) {
            console.log("onload function called")
            // Initialize output box
            output_div = document.getElementById('output')
            output_div.className = "output_parent"
            output_div.innerHTML = `
<div id='outer_edges'> 
<strong>Causes:</strong>
<p id="outer_edges_output" class="output_child"></p>
</div>
<div id='inner_edges'> 
<strong>Caused by:</strong>
<p id="inner_edges_output" class="output_child"></p>
</div>
`
    }
    }
});

