from enum import Enum

MessageType = Enum('done_sending', 'done_receiving', 'notify', 'request', 'exit')

class Message(object):
    # NOTIFY, REQUEST, EXIT, DONE_SENDING, DONE_RECEIVING = range(5)
    SYSTEM_PRIORITY = 0
    OTHER_PRIORITY = 1

    def __init__(self, type_, sender_id, block_id, *payload):
        self.type = type_
        self.sender_id = sender_id
        self.block_id = block_id
        self.payload = payload
        self._priority = (
            self.SYSTEM_PRIORITY
            if self.type in (MessageType.done_sending, MessageType.done_receiving)
            else self.OTHER_PRIORITY
        )

    def __repr__(self):
        return "Message(%s, {%s}, (%d))" % (self.type, self.sender_id, self.block_id)

    def __cmp__(self, other):
        return cmp(self._priority, other._priority)

    def __iter__(self):
        if self.type in [MessageType.done_sending, MessageType.done_receiving]:
            priority = self.SYSTEM_PRIORITY
        else:
            priority = self.OTHER_PRIORITY
        return iter([priority, self])

