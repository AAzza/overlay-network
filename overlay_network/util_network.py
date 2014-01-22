import random

from node import Node, FastNode, Seed

def random_graph(total_nodes, connectivity):
    total_connections = total_nodes * connectivity

    nodes = [Node(i) for i in xrange(1, total_nodes)]
    nodes = [Seed(0)] + nodes
    connections = [[]] * total_nodes
    for i in xrange(total_connections):
        random.shuffle(nodes)
        for i in range(total_nodes):
            curr_node_id = nodes[i].id
            if i != total_nodes:
                next_node_id = nodes[i + 1].id
            else:
                next_node_id = nodes[0].id
            if curr_node_id not in connections[next_node_id]:
                connections[curr_node_id] += next_node_id
                connections[next_node_id] += curr_node_id


