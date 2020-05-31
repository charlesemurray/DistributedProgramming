from distalg import Process, DelayedChannel, Message, Simulation, dispatch, main
import networkx as nx
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

class SafeToken(Message):
    def __init__(self):
        super(SafeToken, self).__init__()

class MsgToken(Message):
    def __init__(self, value):
        super(MsgToken, self).__init__(value=value)

class AckToken(Message):
    def __init__(self):
        super(AckToken, self).__init__()

class PulseToken(Message):
    def __init__(self):
        super(PulseToken, self).__init__()

class ExpectedAcksToken(Message):
    def __init__(self):
        super(ExpectedAcksToken, self).__init__()

class NeighborsSafeToken(Message):
    def __init__(self):
        super(NeighborsSafeToken, self).__init__()


class SynchronizorAlphaProcess(Process):
    def __init__(self, pid=None):
        super(SynchronizorAlphaProcess, self).__init__(pid=pid)
        self.clock = 0
        self.rounds = 5
        self.expected_ack = 0
        self.neighbors_safe = []
        self.is_initiator = False
        self.received_msgs = []
        self.next_pulse_msgs = []
        self.log = logging.getLogger('echo')

    @main
    async def run(self):
        self.log.debug(self.id + " started.")
        await self.loopback_channel.send(PulseToken())
        await self.process_messages()

    @dispatch(PulseToken)
    async def on_receive(self, msg):
        channel = msg.carrier
        if self.rounds > 0:
            self.rounds -= 1
            self.clock += 1
            for k in self.out_channels:
                await k.send(MsgToken(self.clock))
            self.expected_acks = len(self.out_channels)
            self.neighbors_safe = []
            await self.loopback_channel.send(ExpectedAcksToken())
        else:
            self.log.debug("Finished")

    @dispatch(ExpectedAcksToken)
    async def on_receive(self, msg):
        if self.expected_acks == 0:
            for channel in self.out_channels:
                await channel.send(SafeToken())
            await self.loopback_channel.send(NeighborsSafeToken())
        else:
            await self.loopback_channel.send(ExpectedAcksToken())

    @dispatch(NeighborsSafeToken)
    async def on_receive(self, msg):
        if set(self.neighbors_safe) == set(self.neighbors):
            await self.loopback_channel.send(PulseToken())
        else:
            await self.loopback_channel.send(NeighborsSafeToken())



    @dispatch(MsgToken)
    async def on_receive(self, msg):
        channel = msg.carrier
        await channel.back.send(AckToken())
        if not channel.sender in self.neighbors_safe:
            self.received_msgs.append(msg.value)
            print(self.received_msgs)
        else:
            self.next_pulse_msgs.append(msg.value)

    @dispatch(AckToken)
    async def on_receive(self, msg):
        channel = msg.carrier
        self.expected_acks -= 1

    @dispatch(SafeToken)
    async def on_receive(self, msg):
        channel = msg.carrier
        self.neighbors_safe.append(channel.sender)


def test_synchronizor_alpha():
    graph = nx.hypercube_graph(4)  # 4 dimensional
    sm = Simulation(embedding_graph=graph, process_type=SynchronizorAlphaProcess, channel_type=DelayedChannel)
    list(sm.node_map.keys())[1].is_initiator = True

    sm.run(quit_after=4.0)

if __name__ == '__main__':
    test_synchronizor_alpha()
