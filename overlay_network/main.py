import os
import math
import time
import copy
import random
import logging
import argparse

from node import SequenceNode, Seed, RandomNode
from statistics import process_stats, normalize, save_stats, calc_average
from statistics import compare2first


log = logging.getLogger(__name__)


def random_graph(total_nodes, total_connections, node_creator=RandomNode, options=None):
    options = options or {}
    graph = [node_creator(i) for i in xrange(1, total_nodes)]
    graph = [Seed(0, **options)] + graph
    connections = [[] for _ in xrange(total_nodes)]
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


NODES_TYPES = {
    'random': RandomNode,
    'seq': SequenceNode,
}


def simple_graph(seed_options=None):
    seed_options = seed_options or {}
    seed = Seed(0 **seed_options)
    node1 = RandomNode(1)
    node2 = SequenceNode(2)
    node3 = RandomNode(3)
    node1.peers = {0: seed, 3: node3}
    node2.peers = {0: seed, 3: node3}
    node3.peers = {1: node1, 2: node2}
    seed.peers = {1: node1, 2:node2}
    return (seed, node1, node2, node3)


def main(name, nodes, blocks, graph_type='random'):
    seed_options = dict(block_count=blocks)
    if graph_type == 'simple':
        graph = simple_graph(seed_options)
    else:
        total_connections =  int(math.log(nodes, 2)) / 2 + 1
        node_creator = NODES_TYPES[graph_type]
        graph = random_graph(nodes, total_connections,
                             node_creator=node_creator,
                             options=seed_options)
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
    print '-----------------'
    log.info("Average relative delay : %s", calc_average(stats['delay_sub']))
    log.info("Average relative timeout: %s", calc_average(stats['blocks_timeout_sub']))
    log.info("Input speed %s", stats['input_speed'])
    del stats['input_speed']

    stats_dir = os.path.join('out', name)
    if not os.path.exists(stats_dir):
        os.mkdir(stats_dir)
    save_stats(stats, stats_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A program for overlay-network simulation")
    parser.add_argument('name',
                        action='store')
    parser.add_argument('--nodes', '-n',
                        action='store',
                        type=int,
                        default=5)
    parser.add_argument('--blocks', '-b',
                        action='store',
                        type=int,
                        default=20)
    parser.add_argument('--graph_type', '-g',
                        action='store',
                        type=str,
                        default='random',
                        choices=['random', 'sample', 'seq'])
    args = parser.parse_args()

    logging.basicConfig()
    root_logger = logging.getLogger("")
    root_logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(os.path.join('log', args.name+'.log'))
    root_logger.addHandler(file_handler)

    main(**vars(args))
