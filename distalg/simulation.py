import asyncio
import networkx as nx
from distalg.process import Process
from distalg.channel import Channel
from distalg.proxy_process import ProxyProcess


class Simulation:
    def __init__(self, embedding_graph=None, process_types=[Process], channel_type=Channel):

        self.graph = nx.Graph(embedding_graph)
        self.process_map = {}
        self.node_map = {}
        self.channel_map = {}
        self.edge_map = {}
        self.tasks = []

        for n, neighbors_dict in self.graph.adjacency_iter():
            if n not in self.process_map:
                process_n = ProxyProcess(process_types, n)
                self.process_map[n] = process_n
                self.graph.node[n]['process'] = process_n
                self.node_map[process_n] = n
            else:
                process_n = self.process_map[n]

            for neighbor, edge_attr in neighbors_dict.items():
                if neighbor not in self.process_map:
                    process_nbr = ProxyProcess(process_types, neighbor)
                    self.process_map[neighbor] = process_nbr
                    self.graph.node[neighbor]['process'] = process_nbr
                    self.node_map[process_nbr] = neighbor
                else:
                    process_nbr = self.process_map[neighbor]

                channel = channel_type()
                channel._in_end = process_n
                channel._out_end = process_nbr
                channel._sender = process_n.id
                channel._receiver = process_nbr.id

                self.channel_map[(n, neighbor)] = channel
                self.edge_map[channel] = (n, neighbor)
                if (neighbor, n) in self.channel_map:
                    rev_channel = self.channel_map[(neighbor, n)]
                    channel._back = rev_channel
                    rev_channel._back = channel

                process_n.out_channels.add(channel)
                process_nbr.in_channels.add(channel)
                process_n.neighbors.add(process_nbr.id)
                process_nbr.neighbors.add(process_n.id)
            process_n.create_dependent_processes()

    async def start_all(self):
        for process in self.node_map:
            self.tasks += [asyncio.ensure_future(process.run())]
            for internal_process in process.get_internal_processes():
                self.tasks += [asyncio.ensure_future(internal_process.run())]
            for internal_channel in process.get_internal_channels():
                self.tasks += [asyncio.ensure_future(internal_channel.start())]
        self.tasks += [asyncio.ensure_future(channel.start()) for channel in self.edge_map]
        await asyncio.wait(self.tasks)

    def stop_all(self):
        for task in self.tasks:
            task.cancel()

    def processes_iter(self):
        yield from self.node_map  # node map is a dict process: node, this iterates over all the keys i.e. processes

    def run(self, quit_after=10.0):
        loop = asyncio.get_event_loop()
        #loop.set_debug(True)
        loop.call_later(quit_after, self.stop_all)
        loop.run_until_complete(self.start_all())
