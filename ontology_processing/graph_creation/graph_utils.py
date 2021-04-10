def make_acyclic(G):
    """
    Converts a climate mind graph into an acyclic version by removing all the feedback loop edges.
    Paramater:
    G = Networkx graph (Climate Mind graph) created from converting webprotege OWL ontology to networkx graph using functions in make_graph.py
    """
    B = G.copy()
    # identify nodes that are in the class 'feedback loop' then remove those nodes' 'caueses' edges because they start feedback loops.
    # nx.get_node_attributes(B, "direct classes")
    feedback_nodes = list()
    graph_attributes_dictionary = nx.get_node_attributes(B, "direct classes")

    for node in graph_attributes_dictionary:
        if "feedback loop" in graph_attributes_dictionary[node]:
            feedback_nodes.append(node)
    # get the 'causes' edges that lead out of the feedback_nodes
    # must only remove edges that cause increase in greenhouse gases... so only remove edges if the neighbor is of the class 'increase in atmospheric greenhouse gas'
    feedbackloop_edges = list()
    for node in feedback_nodes:
        node_neighbors = B.neighbors(node)
        for neighbor in node_neighbors:
            if (
                "increase in atmospheric greenhouse gas"
                in graph_attributes_dictionary[neighbor]
                or "root cause linked to humans"
                in graph_attributes_dictionary[neighbor]
            ):
                # should make this 'increase in atmospheric greenhouse gas' not hard coded!
                if (
                    B[node][neighbor]["type"] == "causes_or_promotes"
                ):  # should probably make this so the causes_or_promotes isn't hard coded!
                    feedbackloop_edges.append((node, neighbor))

    # remove all the feedback loop edges
    for feedbackloopEdge in feedbackloop_edges:
        nodeA = feedbackloopEdge[0]
        nodeB = feedbackloopEdge[1]
        B.remove_edge(nodeA, nodeB)

    return B


def custom_bfs(graph, start_node, direction="forward", edge_type="causes_or_promotes"):
    """
    Explores graph and gets the subgraph containing all the nodes that are reached via BFS from start_node
    Parameters
    ----------
    graph - nx.DiGraph to explore
    start_node - root of the BFS search
    direction - forward, reverse, or any. Controls what direction BFS searches in
    edge_type - only explore along edges of this type (can be "any")
    Returns
    -------
    subgraph with nodes explored
    """
    # Using a list because we want to have the explored elements returned later.
    queue = [start_node]
    cur_index = 0

    def do_bfs(element):
        nonlocal cur_index
        if direction == "reverse" or direction == "any":
            for start, end, type in graph.in_edges(element, "type"):
                if start not in queue and (edge_type == "any" or type == edge_type):
                    queue.append(start)
        if direction == "forward" or direction == "any":
            for start, end, type in graph.out_edges(element, "type"):
                if end not in queue and (edge_type == "any" or type == edge_type):
                    queue.append(end)

    do_bfs(start_node)

    while cur_index < len(queue):
        do_bfs(queue[cur_index])
        cur_index = cur_index + 1

    return graph.subgraph(queue)