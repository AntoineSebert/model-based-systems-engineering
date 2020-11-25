from __future__ import annotations

import logging
from dataclasses import dataclass, field
from queue import PriorityQueue
from networkx import DiGraph
from logic import Stream, Framelet, Route, Link, Solution, StreamSolution
from typing import List, Tuple
from copy import deepcopy


@dataclass
class Device:
    name: str

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, Device):
            return self.name == other.name
        return False


@dataclass(eq=False)
class Switch(Device):
    queue: PriorityQueue = PriorityQueue()
    speed: float = 1.0

    def emit(self: Switch, time: int) -> None:
        pass

    def receive(self: Switch, time: int) -> set['Stream']:
        misses: set['Stream'] = set()
        temp: PriorityQueue = PriorityQueue()

        while not self.queue.empty():
            priority, framelet = self.queue.get()
            logging.info(f"Switch {self.name} received framelet from {framelet.to_string()}")

            if time < framelet.instance.local_deadline:
                misses.add(framelet.instance.stream)

            self.temp.put((priority, framelet))

        self.queue = temp

        return misses


@dataclass(eq=False)
class EndSystem(Device):
    streams: list[Stream] = field(default_factory=list)
    remainder: int = 0
    ingress: list[Framelet] = field(default_factory=list)  # replace by dict(time, frames)
    egress: list[Framelet] = field(default_factory=list)

    def enqueueStreams(self, network, time): #route argument needed
        # First iteration
        if not time:
            pass # Add all streams
        else:
            index = 0
            for stream in filter(lambda n: not (time % int(n.period)), self.streams):
                size = int(stream.size)
                #print("index", index, " size: ", size)
                while (size > 0):
                    index = index + 1
                    if (size < 64):
                        self.egress.append(Framelet(index, stream.instances, size))
                        size = size - 64
                        print("size2: ", size)
                        print("egress2: ", self.egress)
                    else:
                        self.egress.append(Framelet(index, stream.instances, 64))
                        size = size - 64
                        print("size1: ", size)
                        print("egress1: ", self.egress)
                    

    def emit(self: EndSystem, time: int, network: DiGraph) -> None:
        # todo: check deadline?

        for framelet in self.egress:
            print("\n\n\n\n\nframelet: ", framelet)
            frameDest = framelet.route.dest
            print("\n\n\n\n\nframeDest: ", frameDest)
            network.nodes(frameDest).ingress.append(Framelet)

        logging.info(f"EndSystem {self.name} emitted framelet")


    def receive(self: EndSystem, time: int) -> set['Stream']:
        misses: set['Stream'] = set()

        for framelet in self.ingress:
            logging.info(f"EndSystem {self.name} received framelet from")

        # if time < framelet.instance.local_deadline:
       #	misses.add(framelet.instance.stream)

        self.ingress.clear()

        return misses


@dataclass
class InputPort:
    name: str
    def __hash__(self):
        return hash(self.name)
