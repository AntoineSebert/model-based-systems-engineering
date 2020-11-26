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
    ingress: list[Framelet] = field(default_factory=list)  # replace by dict(time, frames)
    egress: list[Framelet] = field(default_factory=list)

    def __hash__(self):
        # print(hash(self.name))
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, Device):
            return self.name == other.name
        return False


@dataclass(eq=False)
class Switch(Device):
    # queue: PriorityQueue = PriorityQueue()
    speed: float = 1.0

    def emit(self: Switch, time: int, network: DiGraph) -> None:
        pass

    def receive(self: Switch, time: int, network: DiGraph) -> set['Stream']:
        return
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

    def enqueueStreams(self, network, time): #route argument needed
        # First iteration
        index = 0
        for stream in filter(lambda n: not (time % int(n.period)), self.streams):
            # print("Enqueing stream: ", stream.id)
            for route in stream.streamSolution.routes:
                # print("Enqueuing redundant framelets for route:")
                # print(route)
                size = int(stream.size)
                #print("index", index, " size: ", size)
                while (size > 0):
                    index = index + 1
                    if (size < 64):
                        self.egress.append(Framelet(index, stream.instance, size, route))
                        size = size - 64
                    else:
                        self.egress.append(Framelet(index, stream.instance, 64, route))
                        size = size - 64
            stream.instance += 1
                    

    def emit(self: EndSystem, time: int, network: DiGraph) -> None:
        # todo: check deadline?
        # todo: Add time check. emit doesn't care what link speeds are. Emits all framelets on each iteration.
        for i in range(len(self.egress)):
            # print(len(self.egress))
            framelet = self.egress.pop()
            nextStep = next(link for link in framelet.route.links if link.src == self.name)
            nextStep.dest = nextStep.dest.split('$')[0]
            receiver = next(device for device in network._node if device == Device(nextStep.dest))
            receiver.ingress.append(framelet)
            # print("Ingress size: ", len(receiver.ingress))

            device = next(device for device in network._node if device == EndSystem('FRONT_CAM'))

        logging.info(f"EndSystem {self.name} emitted framelet")


    def receive(self: EndSystem, time: int, network: DiGraph) -> set['Stream']:
        pass
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
