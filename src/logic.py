from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from functools import total_ordering
from typing import Union, List

from networkx import DiGraph  # type: ignore

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
