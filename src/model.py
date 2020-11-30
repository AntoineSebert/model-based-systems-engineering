from __future__ import annotations

import logging
from dataclasses import dataclass, field
from queue import PriorityQueue, Queue
from networkx import DiGraph
from copy import deepcopy
from collections.abc import Sequence
from functools import total_ordering

from networkx import DiGraph  # type: ignore


@dataclass
class Device:
    name: str
    ingress: Queue[Framelet] = field(default_factory=Queue)
    egress_main: Queue[Framelet] = field(default_factory=Queue)
    egress_secondary: Queue[Framelet] = field(default_factory=Queue)
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
            if self.egress_main.empty() and self.currentFrame is None:
                break
            if (self.remainingSize <= 0 or self.currentFrame is None):
                self.currentFrame = self.egress_main.get()
                self.remainingSize = self.currentFrame.size
                nextStep = next(link for link in self.currentFrame.route.links if link.src == self.name)
                self.currentSpeed = network.get_edge_data(Device(nextStep.src), InputPort(nextStep.dest))['speed']
                dest = nextStep.dest
                if '$' in nextStep.dest:
                    dest = next(link.dest for link in self.currentFrame.route.links if link.src == nextStep.dest)
                self.currentReceiver = next(device for device in network._node if device == Device(dest))
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
            self.egress_main.put(framelet)    # Queue instead
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
            for route in stream.streamSolution.routes:
                size = int(stream.size)
                index = index + 1
                self.egress_main.put(Framelet(index, stream.instance, size, route, stream, iteration * timeResolution))

            stream.instance += 1


    def emit(self: EndSystem, network: DiGraph, timeResolution: int) -> None:
        # todo: check deadline?
        # todo: Add time check. emit doesn't care what link speeds are. Emits all framelets on each iteration.

        inIteration = 0
        # Framelets(now Frames) from the same stream are not distinguished. Have the same ID
        while (inIteration <= timeResolution):
            if self.egress_main.empty() and self.currentFrame is None:
                break
            if (self.remainingSize <= 0 or self.currentFrame is None):
                self.currentFrame = self.egress_main.get()
                print(self.currentFrame.route)
                self.remainingSize = self.currentFrame.size

                # nextStep = deepcopy(next(link for link in self.currentFrame.route.links if link.src == self.name))
                nextStep = next(link for link in self.currentFrame.route.links if link.src == self.name)
                self.currentSpeed = network.get_edge_data(Device(nextStep.src), InputPort(nextStep.dest))['speed']
                dest = nextStep.dest
                if '$' in nextStep.dest:
                    dest = next(link.dest for link in self.currentFrame.route.links if link.src == nextStep.dest)
                self.currentReceiver = next(device for device in network._node if device == Device(dest))
            sendable = min(self.remainingSize, max((timeResolution - inIteration) * self.currentSpeed, 1.0))
            if inIteration + sendable / self.currentSpeed > timeResolution:  # Can current frame be sent within this simulator iteration?
                break
            # print("In EndSystem")
            # print("Remaining size: ", self.remainingSize)
            # print("Sendable: ", sendable)
            self.remainingSize -= sendable
            # print("Remaining size: ", self.remainingSize)

            inIteration += (float(sendable) / self.currentSpeed)
            self.currentFrame.localTime = inIteration

            if self.remainingSize <= 0:
                # print("Frame delivered")
                self.currentReceiver.ingress.put(self.currentFrame)
                self.currentFrame = None

            # print("\n")
            inIteration += (float(sendable)/self.currentSpeed)

        logging.info(f"EndSystem {self.name} emitted framelet")


    def receive(self: EndSystem, network: DiGraph, time: int, timeResolution: int) -> set['Framelet']:
        misses: set['Framelet'] = set()
        for i in range(self.ingress.qsize()):
            framelet = self.ingress.get()
            logging.info(f"EndSystem {self.name} received framelet from")
            if self.name != framelet.route.links[-1].dest:
                self.egress_main.put(framelet)  # Queue instead
            else: # Check if deadline is passed for frame
                # print("Received frame")
                transmissionTime = time*timeResolution - framelet.releaseTime
                if framelet.stream.WCTT < (transmissionTime):
                    framelet.stream.WCTT = transmissionTime
                if time*timeResolution > framelet.releaseTime + int(framelet.stream.deadline):
                    int(framelet.stream.deadline)
                    time * timeResolution
                    # print("Deadline missed")
                    misses.add(framelet.stream)
        return misses


@dataclass
class InputPort:
    name: str
    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

'''
@dataclass
class Route:
    subgraph: DiGraph

    def check(self: Route) -> None:
        # check if subgraph only is a sequence of nodes, with EndSystem as src and dest
        pass

    def transmission_time(self: Route, size: int) -> int:
        return sum(-(-size // speed) for u, v, speed in self.subgraph.edges(data="speed"))
'''


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
@total_ordering
class Framelet:
    """
    A class used to represent a Framelet

    ...

    Attributes
    ----------
    id : int
        the index of the Framelet within the stream instance
    instance : StreamInstance
        the stream instance the Framelet belongs to
    size : int
        the size of the Framelet
    route : Route
        The list of links that makes up a path in the network
    stream : Stream
        The stream object the framelets was constructed from
    releaseTime : int
        The simulator time at which the framelet was initially released
    localTime : int
        The fraction of time available in current iteration used. Resets to 0 on each simulator iteration

    Methods
    -------
    to_string()
        Returns a short string description of the Framelet
    """

    id: int
    instance: int
    size: int
    route: Route
    stream: Stream
    releaseTime: int
    localTime: float = 0 # Amount of current iteration time used from framelets perspective [assumes units in microseconds]

    def __eq__(self: Framelet, other: object) -> bool:
        if isinstance(other, Framelet):
            if self.instance is not other.instance:
                RuntimeError(f"StreamInstance mismatch between {self=} and {other=}")

            return self.id.__eq__(other.id)
        else:
            return NotImplemented

    def __lt__(self: Framelet, other: object) -> bool:
        if isinstance(other, Framelet):
            if self.instance is not other.instance:
                RuntimeError(f"StreamInstance mismatch between {self=} and {other=}")

            return self.id.__lt__(other.id)
        else:
            return NotImplemented

    def to_string(self: Framelet) -> str:
        """Returns a short string description of the Framelet.

        Parameters
        ----------
        self : Framelet
            The calling instance.

        Returns
        -------
        str
            A short description of the Framelet
        """

        return f"{self.instance.stream.id}[{self.instance.stream.src.name}-{self.instance.stream.dest.name}]/{self.instance.local_deadline}/{self.id}:{self.size}"


@dataclass
@total_ordering
class StreamInstance(Sequence):
    """
    A class used to represent an instance of a Stream

    ...

    Attributes
    ----------
    stream : Stream
        the stream the instance belongs to
    dest : EndSystem
        the destination device
    framelets : list[Framelet]
        the list of framelets of the instance
    local_deadline : int
        the local deadline of the instance

    Methods
    -------
    check_framelets()
        Checks that the sum of the sizes of all framelets is equal to the size of the stream
    """

    stream: Stream
    dest: str
    local_deadline: int
    framelets: list[Framelet] = field(default_factory=list)

    def __getitem__(self: StreamInstance, key: Union[int, slice]) -> Union[Framelet, list[Framelet]]:
        return self.framelets.__getitem__(key)

    def __len__(self: StreamInstance) -> int:
        return self.framelets.__len__()

    def __eq__(self: StreamInstance, other: object) -> bool:
        if isinstance(other, StreamInstance):
            if self.stream is not other.stream:
                RuntimeError(f"Stream mismatch between {self=} and {other=}")

            return self.local_deadline.__eq__(other.local_deadline)
        else:
            return NotImplemented

    def __lt__(self: StreamInstance, other: object) -> bool:
        if isinstance(other, StreamInstance):
            if self.stream is not other.stream:
                RuntimeError(f"Stream mismatch between {self=} and {other=}")

            return self.local_deadline.__lt__(other.local_deadline)
        else:
            return NotImplemented

    def check_framelets(self: StreamInstance) -> int:
        """Checks that the sum of the sizes of all framelets is equal to the size of the stream.

        Returns
        -------
        int
            The subtraction between the length of the sream and the total size of all framelets
        """

        return len(self.stream) - sum(framelet.size for framelet in self.framelets)


@dataclass
@total_ordering
class Stream(Sequence):
    """
    A class used to represent a Stream, with an EDF ordering

    ...

    Attributes
    ----------
    id : str
        the name of the stream
    src : str
        a source device
    dest : str
        name of the destination device
    size : int
        the size of the Stream
    period : int
        the period of the Stream
    deadline : int
        the deadline of the Stream
    rl : int
        a redundancy level
    instances : list[StreamInstance]
        a list of instances
    """

    id: str
    src: str
    dest: str
    size: int
    period: int
    deadline: int
    rl: int
    streamSolution: StreamSolution
    instance: int = 0
    WCTT: int = 0 # Worst-case transmission time detected while simulating


    def __hash__(self: Stream) -> int:
        return hash(self.id)

    def __getitem__(self: Stream, key: Union[int, slice]) -> Union[StreamInstance, list[StreamInstance]]:
        return self.instances.__getitem__(key)

    def __len__(self: Stream) -> int:
        return self.instances.__len__()

    def __eq__(self: Stream, other: object) -> bool:
        if isinstance(other, Stream):
            return self.deadline.__eq__(other.deadline)

        return NotImplemented

    def __lt__(self: Stream, other: object) -> bool:
        if isinstance(other, Stream):
            return self.deadline.__lt__(other.deadline)

        return NotImplemented


@dataclass
class Results:
    """
    A class used to represent a Solution

    ...

    Attributes
    ----------
    network : DiGraph
        a
    streams : set[Stream]
        a set of streams
    routes : dict[Stream, set[Route]]
        a dictionary of streams as keys and set of routes as values
    """

    network: DiGraph
    streams: set[Stream] = field(default_factory=set)
    routes: dict[Stream, set[Route]] = field(default_factory=dict)
