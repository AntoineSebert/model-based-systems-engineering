from __future__ import annotations

import logging
from dataclasses import dataclass, field
from queue import PriorityQueue
from networkx import DiGraph
from logic import Stream, Framelet
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
    ingress: list['Framelet'] = field(default_factory=list)  # replace by dict(time, frames)

    def enqueueStreams(self, network, time):
        # First iteration
        if not time:
            pass # Add all streams
        else:
            for stream in self.streams:
                if not (int(stream.period) % time):
                    pass

    def emit(self: EndSystem, time: int, network: DiGraph) -> None:
        # todo: check deadline?

        for framelet in self.ingress:
            neighbors = network.edges(self)

            for n in neighbors:
                pass
        # print("neigh: ", n, "\n\n\n\n")

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
class Link:
    src: str
    dest: str

    def __hash__(self):
        return hash((self.src, self.dest))

    def __eq__(self, other):
        if isinstance(other, Link) and self.src == other.src and self.dest == other.dest:
            return True
        return False


@dataclass
class Route:
    num: int
    links: List[Link]

    def __hash__(self):
        # print("using hash")
        # print(tuple(self.links))
        # print(hash(tuple(self.links)))
        return hash(tuple(self.links))

    def __eq__(self, other):
        # print("Using eq")
        if isinstance(other, Route) and len(self.links) == len(other.links):
            for index in range(len(self.links)):
                if self.links[index] != other.links[index]:
                    return False
            return True
        return False


@dataclass
class StreamSolution:
    stream: Stream
    routes: List[Route]


@dataclass
class Solution:
    streamSolutions: List[StreamSolution]

    def printSolution(self):
        print("----------------------------------------------")
        print("---------Printing all routes found------------")
        print("----------------------------------------------")
        for streamSolution in self.streamSolutions:
            print()
            print("----------------------------")
            attrs = vars(streamSolution.stream)
            print(', '.join("%s: %s" % item for item in attrs.items()))
            if not streamSolution.routes:
                print("No routes stored for stream!")
            for route in streamSolution.routes:
                print("Route{}:".format(route.num))
                for step in route.links:
                    print(step)
            print("----------------------------")

    def matchRedudancy(self):
        for streamSolution in self.streamSolutions:
            counter = 0
            numberOfRoute = len(streamSolution.routes)
            while len(streamSolution.routes) < int(streamSolution.stream.rl):
                numberOfRoute += 1
                route = deepcopy(streamSolution.routes[counter])
                route.num = numberOfRoute
                streamSolution.routes.append(route)

                if counter == int(streamSolution.stream.rl) - 1:
                    counter = 0
                else:
                    counter += 1
