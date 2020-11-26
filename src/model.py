from __future__ import annotations

import logging
from dataclasses import dataclass, field
from queue import PriorityQueue, Queue
from networkx import DiGraph
from logic import Stream, Framelet, Route, Link, Solution, StreamSolution
from typing import List, Tuple
from copy import deepcopy


@dataclass
class Device:
    name: str
    ingress: Queue[Framelet] = field(default_factory=Queue)
    egress: Queue[Framelet] = field(default_factory=Queue)
    #ingress: list[Framelet] = field(default_factory=list)  # replace by dict(time, frames)
    #egress: list[Framelet] = field(default_factory=list)

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
    # Todo: Change framelet to Frame
    currentFrame: Framelet = None  # Current frame being sent
    remainingSize: int = 0
    currentReceiver: Device = None
    currentSpeed: float = 0.0

    def emit(self: Switch, network: DiGraph, timeResolution) -> None:
        # todo: check deadline?
        # todo: Add time check. emit doesn't care what link speeds are. Emits all framelets on each iteration.

        '''
        for i in range(len(self.egress)):
            # print(len(self.egress))
            framelet = self.egress.pop()
            nextStep = next(link for link in framelet.route.links if link.src == self.name)
            nextStep.dest = nextStep.dest.split('$')[0]
            receiver = next(device for device in network._node if device == Device(nextStep.dest))
            receiver.ingress.append(framelet)
        '''

        iterationTime = timeResolution  # How far a single simulator iterations spans in time in microseconds
        inIteration = 0
        # Framelets(now Frames) from the same stream are not distinguished. Have the same ID
        while (inIteration <= iterationTime):
            if self.egress.empty() and self.currentFrame is None:
                break
            if (self.remainingSize <= 0 or self.currentFrame is None):
                self.currentFrame = self.egress.get()
                self.remainingSize = self.currentFrame.size
                nextStep = deepcopy(next(link for link in self.currentFrame.route.links if link.src == self.name))
                self.currentSpeed = network.get_edge_data(Device(nextStep.src), InputPort(nextStep.dest))['speed']
                if '$' in nextStep.dest:
                    nextStep.dest = next(
                        link.dest for link in self.currentFrame.route.links if link.src == nextStep.dest)
                self.currentReceiver = next(device for device in network._node if device == Device(nextStep.dest))
            sendable = min(self.remainingSize, max((iterationTime - inIteration) * self.currentSpeed, 1.0))

            if inIteration + sendable / self.currentSpeed > iterationTime:  # Can current frame be sent within this simulator iteration?
                break
            # print("In Switch")
            # print("Remaining size: ", self.remainingSize)
            # print("Sendable: ", sendable)
            self.remainingSize -= sendable
            # print("Remaining size: ", self.remainingSize)

            if self.remainingSize <= 0:
                # print("Frame delivered")
                self.currentReceiver.ingress.put(self.currentFrame)
                self.currentFrame = None
            # print("\n")
            inIteration += (float(sendable) / self.currentSpeed)

        logging.info(f"Swtich {self.name} emitted framelet")
        # for i in range(len(self.egress)):
        #     # print(len(self.egress))
        #     framelet = self.egress.pop()
        #     nextStep = next(link for link in framelet.route.links if link.src == self.name)
        #     nextStep.dest = nextStep.dest.split('$')[0]
        #     receiver = next(device for device in network._node if device == Device(nextStep.dest))
        #     receiver.ingress.append(framelet)

    def receive(self: Switch, network: DiGraph, time: int, timeResolution: int) -> set['Stream']:
        misses: set['Framelet'] = set()
        # todo: again careful of order here. Framelets are added to egress in a LIFO manner...
        for i in range(self.ingress.qsize()):
            framelet = self.ingress.get()
            logging.info(f"Switch {self.name} received framelet")
            #if time > framelet.releaseTime + framelet.stream.deadline:
                #misses.add(framelet)
            self.egress.put(framelet)    # Queue instead
        return misses

        # temp: PriorityQueue = PriorityQueue()
        #
        # while not self.queue.empty():
        #     priority, framelet = self.queue.get()
        #     logging.info(f"Switch {self.name} received framelet from {framelet.to_string()}")
        #
        #     if time < framelet.instance.local_deadline:
        #         misses.add(framelet.instance.stream)
        #
        #     self.temp.put((priority, framelet))
        #
        # self.queue = temp
        #
        # return misses


@dataclass(eq=False)
class EndSystem(Device):
    # Todo: Change framelet to Frame
    currentFrame: Framelet = None # Current frame being sent
    remainingSize: int = 0
    currentReceiver: Device = None
    currentSpeed: float = 0.0
    streams: list[Stream] = field(default_factory=list)


    def enqueueStreams(self, network, iteration, timeResolution: int): #route argument needed
        # First iteration
        index = 0
        for stream in filter(lambda n: not (iteration * timeResolution % int(n.period)), self.streams):
            # print("Enqueing stream: ", stream.id, "\nwith period: ", stream.period)
            for route in stream.streamSolution.routes:
                # print("Enqueuing redundant framelets for route:")
                # print(route)
                size = int(stream.size)
                index = 1
                self.egress.put(Framelet(index, stream.instance, size, route, stream, iteration))

            stream.instance += 1
                    

    def emit(self: EndSystem, network: DiGraph, timeResolution: int) -> None:
        # todo: check deadline?
        # todo: Add time check. emit doesn't care what link speeds are. Emits all framelets on each iteration.

        iterationTime = timeResolution # How far a single simulator iterations spans in time in microseconds
        inIteration = 0
        # Framelets(now Frames) from the same stream are not distinguished. Have the same ID
        while (inIteration <= iterationTime):
            if self.egress.empty() and self.currentFrame is None:
                break
            if (self.remainingSize <= 0 or self.currentFrame is None):
                self.currentFrame = self.egress.get()
                self.remainingSize = self.currentFrame.size
                nextStep = deepcopy(next(link for link in self.currentFrame.route.links if link.src == self.name))
                self.currentSpeed = network.get_edge_data(Device(nextStep.src), InputPort(nextStep.dest))['speed']
                if '$' in nextStep.dest:
                    nextStep.dest = next(link.dest for link in self.currentFrame.route.links if link.src == nextStep.dest)
                self.currentReceiver = next(device for device in network._node if device == Device(nextStep.dest))
            sendable = min(self.remainingSize, max((iterationTime - inIteration) * self.currentSpeed, 1.0))

            if inIteration + sendable / self.currentSpeed > iterationTime: # Can current frame be sent within this simulator iteration?
                break
            # print("In EndSystem")
            # print("Remaining size: ", self.remainingSize)
            # print("Sendable: ", sendable)
            self.remainingSize -= sendable
            # print("Remaining size: ", self.remainingSize)

            
            if self.remainingSize <= 0:
                # print("Frame delivered")
                self.currentReceiver.ingress.put(self.currentFrame)
                self.currentFrame = None
            # print("\n")
            inIteration += (float(sendable)/self.currentSpeed)

        logging.info(f"EndSystem {self.name} emitted framelet")


    def receive(self: EndSystem, network: DiGraph, time: int, timeResolution: int) -> set['Stream']:
        misses: set['Framelet'] = set()
        for i in range(self.ingress.qsize()):
            framelet = self.ingress.get()
            logging.info(f"EndSystem {self.name} received framelet from")
            #if time > framelet.releaseTime + framelet.stream.deadline:
                #misses.add(framelet)

        return misses


@dataclass
class InputPort:
    name: str
    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name
