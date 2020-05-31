from distalg import Process, DelayedChannel, Message, Simulation, dispatch, main
import networkx as nx
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

class GoToken(Message):
    def __init__(self, visited):
        super(GoToken, self).__init__(visited=visited)

class BackToken(Message):
    def __init__(self, visited):
        super(BackToken, self).__init__(visited=visited)

class OptimizedDepthFirstTraversalProcess(Process):
    def __init__(self, pid=None):
        super(OptimizedDepthFirstTraversalProcess, self).__init__(pid=pid)
        self.is_initiator = False
        self.children = set()
        self.log = logging.getLogger('echo')
        self.parent_channel = None


    @main
    async def run(self):
        self.log.debug(self.id + " started.")
        if self.is_initiator:
             self.parent_channel = self.id
             self.log.debug(self.id + " initiator.")
             channel = set(self.out_channels).pop()
             await channel.send(GoToken(set(self.in_channels)))
        await self.process_messages()



    @dispatch(GoToken)
    async def on_receive(self, msg):
        channel = msg.carrier
        self.parent_channel = channel
        if set(self.out_channels).issubset(msg.visited):
            await channel.back.send(BackToken(msg.visited.union(set(self.in_channels))))
            self.children = set()
        else:
            k = set(self.out_channels).difference(msg.visited).pop()
            await k.send(GoToken(msg.visited.union(set(self.in_channels))))
            self.children = self.children.union(set([k]))


    @dispatch(BackToken)
    async def on_receive(self, msg):
        channel = msg.carrier
        if set(self.out_channels).issubset(msg.visited):
            if self.is_initiator:
                self.log.debug("Finish.")
            else:
                await self.parent_channel.back.send(BackToken(msg.visited))
        else:
            k = set(self.out_channels).difference(msg.visited).pop()
            await k.send(BackToken(msg.visited))
            self.children = self.children.union(set([k]))




def test_optimized_depth_first_traversal():
    graph = nx.hypercube_graph(4)  # 4 dimensional
    sm = Simulation(embedding_graph=graph, process_type=OptimizedDepthFirstTraversalProcess, channel_type=DelayedChannel)
    list(sm.node_map.keys())[1].is_initiator = True

    sm.run(quit_after=5.0)

if __name__ == '__main__':
    test_optimized_depth_first_traversal()
