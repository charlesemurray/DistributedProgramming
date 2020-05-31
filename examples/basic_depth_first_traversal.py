from distalg import Process, DelayedChannel, Message, Simulation, dispatch, main
import networkx as nx
import asyncio
import logging
from enum import Enum

logging.basicConfig(level=logging.DEBUG)

class GoToken(Message):
    def __init__(self):
        super(GoToken, self).__init__()

class BackToken(Message):
    def __init__(self, response):
        super(BackToken, self).__init__(response=response)

class BackOption(Enum):
    YES = 1
    NO = 2

class BasicDepthFirstTraversalProcess(Process):

    def __init__(self, pid=None):
        super(BasicDepthFirstTraversalProcess, self).__init__(pid=pid)
        self.parent_channel = None
        self.children = set()
        self.visited = set()
        self.is_initiator = False
        self.log = logging.getLogger('echo')

    @main
    async def run(self):
        if self.is_initiator:
            self.log.debug(self.id + "is initiator.")
        self.log.debug(self.id + " started.")
        if self.is_initiator:
            self.parent_channel = self.id
            channel = set(self.out_channels).pop()
            await channel.send(GoToken())
        await self.process_messages()


    @dispatch(GoToken)
    async def on_receive(self, msg):
        channel = msg.carrier
        if self.parent_channel == None:
            self.parent_channel = channel
            self.children = set()
            self.visited = set([channel.back])
            if self.visited == set(self.out_channels):
                await channel.back.send(BackToken(BackOption.YES))
            else:
                k = set(self.out_channels).difference(self.visited).pop()
                await k.send(GoToken())
        else:
            await channel.back.send(BackToken(BackOption.NO))


    @dispatch(BackToken)
    async def on_receive(self, msg):
        channel = msg.carrier
        self.visited = self.visited.union(set([channel.back]))
        if msg.response == BackOption.YES:
            self.children.add(channel)
        if self.visited == set(self.out_channels):
            if self.is_initiator:
                self.log.debug("Finished.")
            else:
                await self.parent_channel.back.send(BackToken(BackOption.YES))
        else:
            k = set(self.out_channels).difference(self.visited).pop()
            await k.send(GoToken())
            



def test_basic_depth_first_traversal():
    graph = nx.hypercube_graph(4)  # 4 dimensional
    sm = Simulation(embedding_graph=graph, process_type=BasicDepthFirstTraversalProcess, channel_type=DelayedChannel)
    list(sm.node_map.keys())[1].is_initiator = True

    sm.run(quit_after=12.0)

if __name__ == '__main__':
    test_basic_depth_first_traversal()
