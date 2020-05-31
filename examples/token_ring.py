from distalg import Process, DelayedChannel, Message, Simulation, dispatch, main
import networkx as nx
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

class GoToken(Message):
    def __init__(self, visited, last):
        super(GoToken, self).__init__(visited=visited, last=last)

class BackToken(Message):
    def __init__(self, visited, last):
        super(BackToken, self).__init__(visited=visited, last=last)

class TokenRingProcess(Process):

    def __init__(self, pid=None):
        super(TokenRingProcess, self).__init__(pid=pid)
        self.routing = {}
        self.succ = None
        self.parent_channel = None
        self.log = logging.getLogger('echo')
        self.first = None
        self.is_initiator = False

    @main
    async def run(self):
        self.log.debug(self.id + " started.")
        if self.is_initiator:
            self.log.debug(self.id + " initiator.")
            self.parent_channel = self.id
            channel = set(self.out_channels).pop()
            self.first = channel.receiver
            await channel.send(GoToken(set([self.id]), self.id))
        await self.process_messages()


    @dispatch(GoToken)
    async def on_receive(self, msg):
        channel = msg.carrier
        self.parent_channel = channel
        self.succ = msg.last
        if set(self.neighbors).issubset(msg.visited):
            await channel.back.send(BackToken(msg.visited.union(set([self.id])), self.id))
            self.routing[channel.sender] = channel.sender
        else:
            k = self.get_out_channels(set(self.neighbors).difference(msg.visited)).pop()
            await k.send(GoToken(msg.visited.union(set([self.id])), self.id))
            self.routing[k.sender] = channel.sender


    @dispatch(BackToken)
    async def on_receive(self, msg):
        channel = msg.carrier
        if set(self.neighbors).issubset(msg.visited):
            if self.is_initiator:
                self.log.debug("Finished.")
            else:
                await self.parent_channel.back.send(BackToken(msg.visited.union(set([self.id])), self.id))
                self.routing[self.parent_channel.sender] = channel.sender
        else:
            k = self.get_out_channels(set(self.neighbors).difference(msg.visited)).pop()
            await k.send(GoToken(msg.visited.union(set([self.id])), self.id))
            self.routing[k.sender] = channel.sender


def test_token_ring():
    graph = nx.hypercube_graph(4)  # 4 dimensional
    sm = Simulation(embedding_graph=graph, process_type=TokenRingProcess, channel_type=DelayedChannel)
    list(sm.node_map.keys())[1].is_initiator = True

    sm.run(quit_after=4.0)

if __name__ == '__main__':
    test_token_ring()
