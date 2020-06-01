from distalg import Process, LoopbackChannel, DelayedChannel, Message, dispatch, main
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

class ProxyProcess(Process):

    def __init__(self, process_types, pid=None):
        super(ProxyProcess, self).__init__(pid=pid)
        self.processes = []
        self.process_routing = {}
        self.token_types = {}
        self.internal_channels = []
        self.is_initiator = False
        self.process_types = process_types
        self.log = logging.getLogger('echo')

    def get_internal_processes(self):
        return self.processes

    def get_internal_channels(self):
        return self.internal_channels

    def create_dependent_processes(self):
        for process_type in self.process_types:
            process = process_type(self.id)
            self.processes.append(process)
            self.token_types.update(process.get_token_types())
            channel = self.create_loopback_channel(process, self)
            rev_channel = self.create_loopback_channel(self, process)
            channel._back = rev_channel
            rev_channel._back = channel
            self.process_routing[type(process)] = rev_channel
            process.loopback_channel = channel
            self.internal_channels += [channel, rev_channel]
            process.out_channels = self.out_channels
            process.in_channels = self.in_channels
            process.neighbors = self.neighbors

    def create_loopback_channel(self, in_end, out_end):
        channel = LoopbackChannel()
        channel._in_end = in_end
        channel._out_end = out_end
        channel._sender = self.id
        channel._receiver = self.id
        return channel

    @dispatch(Message)
    async def on_receive(self, msg):
        process = self.token_types[(type(msg),)]
        channel = self.process_routing[type(process)]
        await channel.forward(msg)

    async def run(self):
        for process in self.processes:
            process.is_initiator = self.is_initiator
        await self.process_messages()

