from __future__ import division

import logging
import random
import time
# from collections import defaultdict

import eventlet
from eventlet.queue import Queue, PriorityQueue

from message import Message, MessageType

log = logging.getLogger(__name__)


class BaseNode(object):

    SIZE = 1024
    INPUT_SPEED = 512
    OUTPUT_SPEED = 512
    # INPUT_SPEED = 10
    # OUTPUT_SPEED = 15
    BUFFER_SIZE = 10
    BITRATE = 256

    def __init__(self, id_):
        self.id = id_
        self._peers = {}
        self.peers_info = {}
        self.available_peers = []
        self.main_channel = PriorityQueue()
        self.data_channel = Queue(1)
        self.sending_queue = Queue()
        self.receiving_queue = Queue()
        self.buffer = {}
        self.stats = {}
        self.received_bytes = 0

    def __repr__(self):
        return "Node(id=%d, peers=%s)" % (self.id, self.peers_info.keys())

    @property
    def peers(self):
        return self._peers

    @peers.setter
    def peers(self, peers):
        self._peers = peers
        self.available_peers = peers.keys()
        self.peers_info = dict((peer_id, []) for peer_id in peers.keys())

    def run(self):
        return eventlet.spawn(self._do_main_loop)

    def _do_main_loop(self):
        sending_thread = eventlet.spawn(self._sending, self.sending_queue, self.main_channel)
        receiving_thread = eventlet.spawn(self._receiving, self.receiving_queue, self.main_channel)
        start_time = time.time()
        while True:
            message = self.main_channel.get()
            block_id = message.block_id
            peer_id = message.sender_id
            log.info("%s: %s" % (self, message))
            if message.type == MessageType.notify:
                self._do_receive_notify(peer_id, block_id)
            elif message.type == MessageType.request:
                self._do_receive_request(peer_id, block_id)
            elif message.type == MessageType.done_sending:
                self._after_sending(peer_id, block_id)
            elif message.type == MessageType.done_receiving:
                self._after_receiving(peer_id, block_id, message.payload[0])
            elif message.type == MessageType.exit:
                self._broadcast(block_id, MessageType.exit)
                sending_thread.kill()
                receiving_thread.kill()
                break
            self._try_to_request()
            eventlet.sleep(0)
            log.debug("%s: available peers - %s" % (self, self.available_peers))
        end_time = time.time()
        self.stats['input_speed'] = self.received_bytes / (end_time - start_time)
        return self.stats

    def _sending(self, queue, back_queue):
        while True:
            block_id, receiver_id, part = queue.get()
            receiver = self.peers[receiver_id]
            if receiver.data_channel.full():
                queue.put((block_id, receiver.id, part))
                eventlet.sleep(0)
                continue
            # log.debug("Send %d/%d of %d to %d" %(part+1, self.SIZE, block_id, receiver_id))
            receiver.data_channel.put((block_id, self.id, part))
            if part < self.SIZE - 1:
                queue.put((block_id, receiver_id, part + 1))
            else:
                back_queue.put(Message(MessageType.done_sending, receiver_id, block_id))
            eventlet.sleep(1/self.OUTPUT_SPEED)

    def _receiving(self, queue, back_queue):
        while True:
            block_id, sender_id, part = self.data_channel.get()
            # log.debug("%s: Get %d/%d of %d to %d" % (self, part+1, self.SIZE, block_id, sender_id))
            self.received_bytes += self.SIZE
            if part == self.SIZE - 1:
                back_queue.put(Message(MessageType.done_receiving, sender_id, block_id, block_id))
            eventlet.sleep(1/self.INPUT_SPEED)

    def _after_receiving(self, sender_id, block_id, block):
        # if len(self.buffer) == self.BUFFER_SIZE:
        #     ids = sorted(self.buffer)
        #     del self.buffer[ids[0]]
        self.buffer[block_id] = block
        if sender_id != self.id:
            self.available_peers.append(sender_id)
        blocks_stats = self.stats.setdefault('blocks_timeout', {})
        blocks_stats[block_id] = time.time()
        self._broadcast(block_id, MessageType.notify)

    def _do_receive_notify(self, sender_id, block_id):
        # self.peers[sender_id].main_channel.put(Message(Message.REQUEST, self.id, block_id))
        log.info("%s: Notify about (%d) from {%d}" % (self, block_id, sender_id))

    def _do_receive_request(self, sender_id, block_id):
        # assert (sender_id in self.available_peers), "only one connection between peers"
        assert (block_id in self.buffer.keys()), "WTF?!"
        if sender_id not in self.available_peers:
            self.main_channel.put(Message(MessageType.request, sender_id, block_id))
            eventlet.sleep(0)
            return
        self.available_peers.remove(sender_id)
        self.sending_queue.put((block_id, sender_id, 0))

    def _after_sending(self, receiver_id, block_id):
        self.available_peers.append(receiver_id)

    def _try_to_request(self):
        raise NotImplementedError

    def _broadcast(self, block_id, message_type):
        for peer in self.peers.values():
            peer.main_channel.put(Message(message_type, self.id, block_id))


class Seed(BaseNode):

    OUTPUT_SPEED = 1024

    def __init__(self,  *args, **kwargs):
        self.BLOCKS_COUNT = kwargs.pop('block_count', 10)
        super(Seed, self).__init__(*args, **kwargs)

    def _do_receive_notify(self, sender_id, block_id):
        pass

    def _receiving(self, queue, back_queue):
        block_id = 0
        while block_id < self.BLOCKS_COUNT:
            eventlet.sleep(self.SIZE/self.BITRATE)
            log.info("%s: Generate new block %d" % (self, block_id))
            back_queue.put(Message(MessageType.done_receiving, self.id, block_id, block_id + 100))
            block_id += 1
        back_queue.put(Message(MessageType.exit, self.id, block_id))

    def _try_to_request(self):
        pass


class Node(BaseNode):
    # INPUT_SPEED = 10

    def __init__(self, *args, **kwargs):
        super(Node, self).__init__(*args, **kwargs)
        self.want_them = []

    def _do_receive_notify(self, sender_id, block_id):
        self.peers_info[sender_id].append(block_id)
        if block_id not in self.want_them and block_id not in self.buffer.keys():
            self.want_them.append(block_id)

    def _after_sending(self, sender_id, block_id):
        super(Node, self)._after_sending(sender_id, block_id)

    def _try_to_request(self):
        log.debug("%s: peers_info - %s" % (self, self.peers_info))
        shuffled_blocks = random.sample(self.want_them, len(self.want_them))
        shuffled_peers = random.sample(self.available_peers, len(self.available_peers))
        for block_id in shuffled_blocks:
            for peer_id in shuffled_peers:
                if block_id in self.peers_info[peer_id]:
                    self.want_them.remove(block_id)
                    self.available_peers.remove(peer_id)
                    log.info("%s: sending request to %d" % (self, peer_id))
                    self.peers[peer_id].main_channel.put(Message(MessageType.request, self.id, block_id))
                    return


class FastNode(Node):
    # INPUT_SPEED = 10

    def _try_to_request(self):
        log.debug("%s: peers_info - %s" % (self, self.peers_info))
        shuffled_blocks = sorted(self.want_them)
        shuffled_peers = random.sample(self.available_peers, len(self.available_peers))
        for block_id in shuffled_blocks:
            for peer_id in shuffled_peers:
                if block_id in self.peers_info[peer_id]:
                    self.want_them.remove(block_id)
                    self.available_peers.remove(peer_id)
                    log.info("%s: sending request to %d" % (self, peer_id))
                    self.peers[peer_id].main_channel.put(Message(MessageType.request, self.id, block_id))
                    return

class MiddleNode(Node):
    # INPUT_SPEED = 10

    def _try_to_request(self):
        log.debug("%s: peers_info - %s" % (self, self.peers_info))
        shuffled_blocks = sorted(self.want_them)
        shuffled_peers = random.sample(self.available_peers, len(self.available_peers))
        for peer_id in shuffled_peers:
            for block_id in shuffled_blocks:
                if block_id in self.peers_info[peer_id]:
                    self.want_them.remove(block_id)
                    self.available_peers.remove(peer_id)
                    log.info("%s: sending request to %d" % (self, peer_id))
                    self.peers[peer_id].main_channel.put(Message(MessageType.request, self.id, block_id))
                    return
