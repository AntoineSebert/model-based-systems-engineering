from __future__ import annotations

import logging
from dataclasses import dataclass, field
from queue import PriorityQueue, Queue
from networkx import DiGraph
from copy import deepcopy
from collections.abc import Sequence
from functools import total_ordering

from networkx import DiGraph  # type: ignore

@total_ordering
@dataclass
class Device:
    name: str
    localTime: float = 0.0
    ingress: Queue[Framelet] = field(default_factory=Queue)
    egress_main: Queue[Framelet] = field(default_factory=Queue)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, Device):
            return self.name == other.name
        return False

    def __lt__(self, other):
        if isinstance(other, Device):
            return self.localTime < other.localTime
        else:
            RuntimeError(f"Mismatch between device {self=} and other {other=}")

    # We always advance time by the guard band!
    def emit(self, network: DiGraph) -> None:
        if not self.egress_main.empty():
            frame = self.egress_main.get()
            nextStep = next(link for link in frame.route.links if link.src == self.name)
            speed = network.get_edge_data(Device(nextStep.src), Device(nextStep.dest))['speed']
            receiver = next(device for device in network._node if device == Device(nextStep.dest))

            # advance time for this device and the frame sent
            self.localTime += 64.0 / speed
            frame.localTime += self.localTime
            receiver.ingress.put(frame) # Send framelet
        else:
            self.localTime += 64 / 12.5


        logging.info(f"Swtich {self.name} emitted framelet")


@dataclass(eq=False)
class Switch(Device):
    def receive(self: Switch) -> set['Framelet']:
        misses: set['Framelet'] = set()
        for i in range(self.ingress.qsize()):
            framelet = self.ingress.get()
            logging.info(f"Switch {self.name} received framelet")
            self.egress_main.put(framelet)  # Queue instead
        return misses


@dataclass(eq=False)
class EndSystem(Device):
    streams: list[Stream] = field(default_factory=list)

    def enqueueStreams(self, network, iteration, timeResolution: int):  # route argument needed
        # First iteration
        index = 0
        for stream in filter(lambda n: not (iteration * timeResolution % int(n.period)), self.streams):
            for route in stream.streamSolution.routes:
                size = int(stream.size)
                index = index + 1
                self.egress_main.put(Framelet(index, stream.instance, size, route, stream, iteration * timeResolution))
            stream.instance += 1

    def receive(self: EndSystem) -> set['Stream']:
        misses: set['Stream'] = set()
        for i in range(self.ingress.qsize()):
            framelet = self.ingress.get()
            logging.info(f"EndSystem {self.name} received framelet from")
            if self.name != framelet.route.links[-1].dest:
                self.egress_main.put(framelet)  # Queue instead
            else:  # Check if deadline is passed for frame
                if framelet.stream_instance.stream.WCTT < framelet.localTime - framelet.stream_instance.release_time:
                    framelet.stream_instance.stream.WCTT = framelet.localTime - framelet.stream_instance.release_time
                if framelet.localTime > framelet.stream_instance.local_deadline:
                    misses.add(framelet.stream_instance.stream)
        return misses


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
    routes: list['Route']


@dataclass
class Solution:
    streamSolutions: list['StreamSolution']

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
    links: list['Link']

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
    currentDevice : Device
        The framelet's current location in the network, i.e. the egress port in which the framelet is currently residing
    localTime : int
        The fraction of time available in current iteration used. Resets to 0 on each simulator iteration
    priority : int
        The priority of the framelet. Assumes values 1-8

    Methods
    -------
    to_string()
        Returns a short string description of the Framelet
    """
    index: int
    stream_instance: StreamInstance
    size: int
    localTime: float
    route: Route
    priority: int = 1

    def __eq__(self: Framelet, other: object) -> bool:
        if isinstance(other, Framelet):
            if self.instance is not other.instance:
                RuntimeError(f"StreamInstance mismatch between {self=} and {other=}")
            return self.stream_instance == other.stream_instance and self.index == other.index and self.priority == other.priority
        else:
            RuntimeError(f"Expectedd StreamInstance {other=} to be of type Framelet")

    def __lt__(self: Framelet, other: object) -> bool:
        # Relevant for egress priority queues
        if isinstance(other, Framelet):
            return self.priority > other.priority
        else:
            RuntimeError(f"Expectedd StreamInstance {other=} to be of type Framelet")

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
    local_deadline : int
        the local deadline of the instance
    framelets : list[Framelet]
        the list of framelets of the instance

    Methods
    -------
    check_framelets()
        Checks that the sum of the sizes of all framelets is equal to the size of the stream
    """

    stream: Stream
    dest: str
    instance: int
    release_time: int
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

    def create_framelets(self):
        # This puts the frames in order by a route basis. Could be changed to put frames in queue on an index basis
        for route in self.stream.streamSolution.routes:
            size = int(self.stream.size)
            index = 0
            while (size > 0):
                if (size < 64):
                    self.framelets.append(Framelet(index, self, size, self.release_time, route))
                else:
                    self.framelets.append(Framelet(index, self, 64, self.release_time, route))
                size = size - 64
                index += 1

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
    device: Device
    streamSolution: StreamSolution
    WCTT: int = 0  # Worst-case transmission time detected while simulating

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
