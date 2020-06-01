from distalg import Process, DelayedChannel, Message, Simulation, dispatch, main
import networkx as nx
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)


class GoToken(Message):
    def __init__(self, data):
        super(GoToken, self).__init__(data=data)

class BackToken(Message):
    def __init__(self, val_set):
        super(BackToken, self).__init__(val_set=val_set)


class SpanningTreeProcess(Process):
    def __init__(self, pid=None):
        super(SpanningTreeProcess, self).__init__(pid = pid)
        self.parent = None
        self.parent_channel = None
        self.children = set()
        self.expected_msg = len(self.out_channels)
        self.is_initiator = False
        self.val_set = set()
        self.log = logging.getLogger('spanning tree')

    @main
    async def run(self):
        self.log.debug(self.id + " started.")
        if self.is_initiator:
            self.parent_channel = self.id
            self.expected_msg = len(self.out_channels)
            self.log.debug(self.out_channels)
            for channel in self.out_channels:
                await channel.send(GoToken(self.id))
        await self.process_messages()

    @dispatch(GoToken)
    async def on_receive(self, msg):
        channel = msg.carrier
        if self.parent_channel == None:
            self.parent_channel = channel
            self.children = set()
            self.expected_msg = len(self.out_channels) - 1
            if self.expected_msg == 0:
                await channel.back.send(BackToken(set((self.id, 1024))))
            else:
                for k in set(self.out_channels).difference(set([channel.back])):
                    await k.send(GoToken(self.id))
        else:
            await channel.back.send(BackToken(set()))

    @dispatch(BackToken)
    async def on_receive(self, msg):
        self.expected_msg -= 1
        channel = msg.carrier
        if len(msg.val_set) != 0:
            self.children.add(channel)
            self.val_set = self.val_set.union(msg.val_set)
        if self.expected_msg == 0:
            self.val_set.add((self.id, 1024))
            if not self.is_initiator:
                await self.parent_channel.back.send(BackToken(self.val_set))
            else:
                self.log.debug(str(self.val_set) + " val_set")

def test_spanning_tree():
    graph = nx.hypercube_graph(4)  # 4 dimensional
    sm = Simulation(embedding_graph=graph, process_types=[SpanningTreeProcess], channel_type=DelayedChannel)
    list(sm.node_map.keys())[0].is_initiator = True
    #for a in sm.node_map:
    #    a.is_initiator = True
    #    break

    sm.run(quit_after=4.0)

if __name__ == '__main__':
    test_spanning_tree()
