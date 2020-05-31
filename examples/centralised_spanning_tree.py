from distalg import Process, DelayedChannel, Message, Simulation, dispatch, main
import networkx as nx
import asyncio
import logging
from enum import Enum

logging.basicConfig(level=logging.DEBUG)

class GoToken(Message):
    def __init__(self, depth):
        super(GoToken, self).__init__(depth=depth)

class BackToken(Message):
    def __init__(self, response):
        super(BackToken, self).__init__(response=response)

class BackOption(Enum):
    STOP = 1
    CONTINUE = 2
    NO = 3

class CentralisedSpanningTreeProcess(Process):

    def __init__(self, pid=None):
        super(CentralisedSpanningTreeProcess, self).__init__(pid=pid)
        self.parent_channel = None
        self.expected_msg = 0
        self.level = 0
        self.children = set()
        self.send_to = set()
        self.waiting_from = set()
        self.is_initiator = False
        self.log = logging.getLogger('echo')

    @main
    async def run(self):
        self.log.debug(self.id + " started.")
        if self.is_initiator:
            self.parent_channel = self.id
            self.send_to = set(self.out_channels)
            self.waiting_from = set(self.out_channels)
            for channel in self.out_channels:
                await channel.send(GoToken(0))
        await self.process_messages()

    @dispatch(GoToken)
    async def on_receive(self, msg):
        channel = msg.carrier
        if self.parent_channel == None:
            self.parent_channel = channel
            self.level = msg.depth + 1
            self.children = set()
            self.send_to = set(self.out_channels).difference(set([channel.back]))
            if len(self.send_to) == 0:
                await channel.back.send(BackToken(BackOption.STOP))
            else:
                await channel.back.send(BackToken(BackOption.CONTINUE))
        elif self.parent_channel == channel:
            for k in self.send_to:
                await k.send(GoToken(self.level))
            self.waiting_from = self.send_to.copy()
        else:
            await channel.back.send(BackToken(BackOption.NO))


    @dispatch(BackToken)
    async def on_receive(self, msg):
        channel = msg.carrier
        self.waiting_from.remove(channel.back)
        if msg.response == BackOption.STOP:
            self.children.add(channel)
            self.send_to.remove(channel.back)
        elif msg.response == BackOption.CONTINUE:
            self.children.add(channel)
        else:
            self.send_to.remove(channel.back)
        if len(self.waiting_from) == 0:
            if len(self.send_to) == 0:
                if self.is_initiator:
                    self.log.debug("Finished.")
                else:
                    await self.parent_channel.back.send(BackToken(BackOption.STOP))
            else:
                if self.is_initiator:
                    for k in self.send_to:
                        await k.send(GoToken(self.level))
                    self.waiting_from = self.send_to.copy()
                else:
                    await self.parent_channel.back.send(BackToken(BackOption.CONTINUE))







def test_centralised_spanning_tree():
    graph = nx.hypercube_graph(4)  # 4 dimensional
    sm = Simulation(embedding_graph=graph, process_type=CentralisedSpanningTreeProcess, channel_type=DelayedChannel)
    list(sm.node_map.keys())[1].is_initiator = True

    sm.run(quit_after=4.0)

if __name__ == '__main__':
    test_centralised_spanning_tree()
