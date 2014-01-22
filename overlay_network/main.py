import logging
import pprint
import math
import os
import time
import copy

import random
from consoleargs import command

from node import Node, FastNode, Seed, MiddleNode
from statistics import process_stats, normalize, save_stats, calc_average

log = logging.getLogger(__name__)

# class Node(object):
#     def __init__(self, id_):
#         self.id = id_
#
# class Seed(Node):
#     pass

def random_graph(total_nodes, total_connections, node_creator=Node, options={}):
    graph = [node_creator(i) for i in xrange(1, total_nodes)]
    graph = [Seed(0, **options)] + graph
    connections = [[] for _ in xrange(total_nodes)]
    # import pdb; pdb.set_trace()
    nodes = graph[:]
    for i in xrange(total_connections):
        random.shuffle(nodes)
        for i in xrange(total_nodes):
            curr_node_id = nodes[i].id
            if i < total_nodes - 1:
                next_node_id = nodes[i + 1].id
            else:
                next_node_id = nodes[0].id
            if curr_node_id not in connections[next_node_id]:
                connections[curr_node_id] += [next_node_id]
                connections[next_node_id] += [curr_node_id]
    for node in graph:
        node.peers = dict(((peer_id, graph[peer_id]) for peer_id in connections[node.id]))
    return graph


def simple_graph():
    seed = Seed(0)
    node1 = Node(1)
    node2 = FastNode(2)
    node3 = Node(3)
    node1.peers = {0: seed, 3: node3}
    node2.peers = {0: seed, 3: node3}
    node3.peers = {1: node1, 2: node2}
    seed.peers = {1: node1, 2:node2}
    return (seed, node1, node2, node3)


def compare2first(stats):
    new_stats = {}
    for key, value in stats.iteritems():
        new_stats[key] = {}
        for inner_key, inner_value in value.iteritems():
            new_stats[key][inner_key] = inner_value - stats[0][inner_key]
    return new_stats


@command
def main(count=5, block_count=20):
    # graph = simple_graph()
    graph = random_graph(count, int(math.log(count, 2)) / 2 + 1, node_creator=MiddleNode, options=dict(block_count=block_count))
    log.info(graph)
    start_time = time.time()
    threads = [(node.id, node.run()) for node in graph]
    stats = {}
    for node_id, thread in threads:
        stats[node_id] = thread.wait()

    stats = process_stats(stats)

    stats['delay'] = copy.deepcopy(stats['blocks_timeout'])
    for key, value in stats['delay'].iteritems():
        for inner_key, inner_value in value.iteritems():
            value[inner_key] -= start_time

    stats = normalize(stats, ['blocks_timeout'])
    stats['blocks_timeout_sub'] = compare2first(stats['blocks_timeout'])
    stats['delay_sub'] = compare2first(stats['delay'])
    # pprint.pprint(stats)
    print '-----------------'
    print calc_average(stats['delay_sub'])
    print calc_average(stats['blocks_timeout_sub'])
    print stats['input_speed']
    del stats['input_speed']
    save_stats(stats)


if __name__ == '__main__':
    logging.basicConfig()
    root_logger = logging.getLogger("")
    root_logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(os.path.join('log', str(int(time.time()))))
    root_logger.addHandler(file_handler)

    main()

