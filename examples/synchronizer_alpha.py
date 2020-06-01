from distalg import Process, DelayedChannel, Message, CallbackMessage, Simulation, dispatch, main
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

class SynchronizerAlphaProcess(Process):
    def __init__(self, pid=None):
        super(SynchronizerAlphaProcess, self).__init__(pid=pid)
        self.clock = 0
        self.rounds = 5
        self.expected_ack = 0
        self.neighbors_safe = set()
        self.is_initiator = False
        self.received_msgs = []
        self.next_pulse_msgs = []
        self.log = logging.getLogger('echo')

    @main
    async def run(self):
        self.log.debug(self.id + " started.")
        print(self.neighbors)
        print(self.loopback_channel)
        await self.loopback_channel.send(PulseToken())
        await self.process_messages()

    @dispatch(PulseToken)
    async def on_receive(self, msg):
        print("PulseToken")
        channel = msg.carrier
        if self.rounds > 0:
            self.rounds -= 1
            self.clock += 1
            for k in self.out_channels:
                await k.send(MsgToken(self.clock))
            self.expected_acks = len(self.out_channels)
            self.neighbors_safe = set()
            await self.loopback_channel.send(CallbackMessage(function=self.check_expected_acks))
        else:
            self.log.debug("Finished")

    async def check_expected_acks(self, msg):
        print("ExpectedAcks")
        if self.expected_acks == 0:
            for channel in self.out_channels:
                await channel.send(SafeToken())
            await self.loopback_channel.send(self.check_neighbors_safe())
        else:
            await self.loopback_channel.send(CallBackToken(function=self.check_expected_acks))

    async def check_neighbors_safe(self, msg):
        print("NeghborsSafe")
        if self.neighbors_safe == self.neighbors:
            await self.loopback_channel.send(PulseToken())
        else:
            await self.loopback_channel.send(CallbackMessage(function=self.check_neighbors_safe))




    @dispatch(MsgToken)
    async def on_receive(self, msg):
        #print("MsgToken")
        channel = msg.carrier
        await channel.back.send(AckToken())
        if not channel.sender in self.neighbors_safe:
            self.received_msgs.append(msg.value)
            print(self.received_msgs)
        else:
            self.next_pulse_msgs.append(msg.value)

    @dispatch(AckToken)
    async def on_receive(self, msg):
        #print("AckToken")
        channel = msg.carrier
        self.expected_acks -= 1

    @dispatch(SafeToken)
    async def on_receive(self, msg):
        #print("SafeToken")
        channel = msg.carrier
        print("Neighbors")
        print(self.neighbors)
        print("Out Channels")
        print([channel.receiver for channel in self.out_channels])
        print(self.id)
        print("Safe Neighbors")
        print(self.neighbors_safe)
        self.neighbors_safe.add(channel.sender)


def test_synchronizer_alpha():
    graph = nx.hypercube_graph(4)  # 4 dimensional
    sm = Simulation(embedding_graph=graph, process_types=[SynchronizerAlphaProcess], channel_type=DelayedChannel)
    list(sm.node_map.keys())[1].is_initiator = True

    sm.run(quit_after=4.0)

if __name__ == '__main__':
    test_synchronizer_alpha()
