from distalg import Process, DelayedChannel, Message, Simulation, dispatch, main
import networkx as nx
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

class UpdateToken(Message):
    def __init__(self, length):
        super(UpdateToken, self).__init__(length=length)

class BellFordShortedPathProcess(Process):

    def __init__(self, pid=None):
        super(BellFordShortedPathProcess, self).__init__(pid=pid)
        self.is_initiator = False
        self.routing_to = {}
        self.updated = False
        self.length = {}
        self.log = logging.getLogger('echo')

    @main
    async def run(self):
        self.log.debug(self.id + " started.")
        if self.is_initiator:
            self.log.debug(self.id + " initiator.")
            

    @dispatch(UpdateToken)
    async def on_receive(self, msg):
        channel = msg.carrier


def test_echo():
    graph = nx.hypercube_graph(4)  # 4 dimensional
    sm = Simulation(embedding_graph=graph, process_type=TerminatingEchoProcess, channel_type=DelayedChannel)
    list(sm.node_map.keys())[1].is_initiator = True

    sm.run(quit_after=4.0)

if __name__ == '__main__':
    test_echo()