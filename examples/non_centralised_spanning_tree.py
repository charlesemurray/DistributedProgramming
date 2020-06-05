from distalg import Process, DelayedChannel, Message, Simulation, dispatch, main
import networkx as nx
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

class GoToken(Message):
    def __init__(self, depth):
        super(GoToken, self).__init__(depth=depth)

class BackToken(Message):
    def __init__(self, response, depth):
        super(BackToken, self).__init__(response=response, depth=depth)

class NonCentralisedSpanningTreeProcess(Process):
    def __init__(self, pid=None):
        super(NonCentralisedSpanningTreeProcess, self).__init__(pid=pid)
        self.parent_channel = None
        self.children = set()
        self.expected_msg = 0
        self.level = 0
        self.is_initiator = False
        self.log = logging.getLogger('echo')

    @main
    async def run(self):
        self.log.debug(self.id + " started.")
        if self.is_initiator:
            self.expected_msg = len(self.out_channels)
            for channel in self.out_channels:
                await channel.send(GoToken(0))
        await self.process_messages()

    @dispatch(GoToken)
    async def on_receive(self, msg):
        channel = msg.carrier
        if self.parent_channel == None:
            self.level = msg.depth + 1
            self.parent_channel = channel
            self.children = set()
            self.expected_msg = len(self.out_channels) - 1
            if self.expected_msg == 0:
                await channel.back.send(BackToken(True, self.level))
            else:
                for k in set(self.out_channels).difference(set([channel.back])):
                    await k.send(GoToken(msg.depth + 1))
        elif self.level > msg.depth + 1:
            self.parent_channel = channel
            self.level = msg.depth + 1
            self.children = set()
            self.expected_msg = len(self.out_channels) - 1
            if self.expected_msg == 0:
                await channel.back.send(BackToken(True, self.level))
            else:
                for k in set(self.out_channels).difference(set([channel.back])):
                    await k.send(GoToken(msg.depth + 1))
        else:
            await channel.back.send(BackToken(False, msg.depth + 1))

    @dispatch(BackToken)
    async def on_receive(self, msg):
        channel = msg.carrier
        if self.level == msg.depth - 1:
            if msg.response:
                self.children.add(channel)
            self.expected_msg -= 1
            if self.expected_msg == 0:
                if self.is_initiator:
                    self.log.debug("Finished")
                else:
                    await self.parent_channel.back.send(BackToken(True, self.level))


def test_non_centralised_spanning_tree():
    graph = nx.hypercube_graph(4)  # 4 dimensional
    sm = Simulation(embedding_graph=graph, process_types=[NonCentralisedSpanningTreeProcess], channel_type=DelayedChannel)
    print(sm.node_map.keys())
    list(sm.node_map.keys())[0].is_initiator = True
    #for a in sm.node_map:
    #    a.is_initiator = True
    #    break

    sm.run(quit_after=4.0)

if __name__ == '__main__':
    test_non_centralised_spanning_tree()
