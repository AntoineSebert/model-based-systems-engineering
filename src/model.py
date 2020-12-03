from __future__ import annotations

import logging
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from functools import total_ordering
from queue import PriorityQueue, Queue
from xml.etree.ElementTree import Element

from networkx import DiGraph  # type: ignore


@dataclass
class Device:
	name: str
	ingress: Queue[Framelet] = field(default_factory=Queue) # make into list
	egress: Queue[Framelet] = field(default_factory=Queue) # make into pqueue

	def __hash__(self: Device) -> int:
		return hash(self.name)

	def __eq__(self: Device, other: object) -> bool:
		if isinstance(other, Device):
			return self.name == other.name

		return False


@dataclass(eq=False)
class Switch(Device):
	speed: float = 1.0
	currentFrame: Framelet = None
	remainingSize: int = 0
	currentReceiver: Device = None
	currentSpeed: float = 0.0

	def emit(self: Switch, network: DiGraph, timeResolution: int) -> None:
		iterationTime = timeResolution
		inIteration = 0

		while (inIteration <= iterationTime):
			if self.egress.empty() and self.currentFrame is None:
				break

			if (self.remainingSize <= 0 or self.currentFrame is None):
				self.currentFrame = self.egress.get()
				self.remainingSize = self.currentFrame.size
				nextStep = next(link for link in self.currentFrame.route.links if link.src == self)
				self.currentSpeed = network.get_edge_data(nextStep.src, nextStep.dest)['speed']

				if '$' in nextStep.dest.name:
					nextStep.dest = next(link.dest for link in self.currentFrame.route.links if link.src == nextStep.dest)

				self.currentReceiver = next(device for device in network._node if device == nextStep.dest)

			sendable = min(self.remainingSize, max((iterationTime - inIteration) * self.currentSpeed, 1.0))

			if inIteration + sendable / self.currentSpeed > iterationTime:
				break

			self.remainingSize -= sendable

			if self.remainingSize <= 0:
				self.currentReceiver.ingress.put(self.currentFrame)
				self.currentFrame = None

			inIteration += (float(sendable) / self.currentSpeed)

		logging.info(f"Swtich {self.name} emitted framelet")

	def receive(self: Switch, network: DiGraph, time: int, timeResolution: int) -> set['Stream']:
		misses: set['Framelet'] = set()

		for i in range(self.ingress.qsize()):
			framelet = self.ingress.get()
			logging.info(f"Switch {self.name} received framelet")
			self.egress.put(framelet)

		return misses


@dataclass(eq=False)
class EndSystem(Device):
	currentFrame: Framelet = None
	remainingSize: int = 0
	currentReceiver: Device = None
	currentSpeed: float = 0.0
	streams: list[Stream] = field(default_factory=list)

	def enqueueStreams(self: EndSystem, network: DiGraph, iteration: int, timeResolution: int) -> None:
		index = 0

		for stream in self.streams:
			for route in stream.routes:
				index = index + 1
				self.egress.put(Framelet(index, stream.instance, stream.size, route, stream, iteration * timeResolution))

			stream.instance += 1

	def emit(self: EndSystem, network: DiGraph, timeResolution: int) -> None:
		iterationTime = timeResolution
		inIteration = 0

		while inIteration <= iterationTime:
			if self.egress.empty() and self.currentFrame is None:
				break

			if (self.remainingSize <= 0 or self.currentFrame is None):
				self.currentFrame = self.egress.get()
				self.remainingSize = self.currentFrame.size

				nextStep = next(link for link in self.currentFrame.route.links if link.src == self)

				self.currentSpeed = network.get_edge_data(nextStep.src, nextStep.dest)['speed']

				if '$' in nextStep.dest.name:
					nextStep.dest = next(link.dest for link in self.currentFrame.route.links if link.src == nextStep.dest)

				self.currentReceiver = next(device for device in network._node if device == nextStep.dest)

			sendable = min(self.remainingSize, max((iterationTime - inIteration) * self.currentSpeed, 1.0))

			if inIteration + sendable / self.currentSpeed > iterationTime:
				break

			self.remainingSize -= sendable

			if self.remainingSize <= 0:
				self.currentReceiver.ingress.put(self.currentFrame)
				self.currentFrame = None

			inIteration += (float(sendable) / self.currentSpeed)

		logging.info(f"EndSystem {self.name} emitted framelet")

	def receive(self: EndSystem, network: DiGraph, time: int, timeResolution: int) -> set['Framelet']:
		misses: set['Framelet'] = set()

		for i in range(self.ingress.qsize()):
			framelet = self.ingress.get()
			logging.info(f"EndSystem {self.name} received framelet from")

			if self != framelet.route.links[-1].dest:
				self.egress.put(framelet)
			else:
				transmissionTime = time * timeResolution - framelet.releaseTime

				if framelet.stream.WCTT < (transmissionTime):
					framelet.stream.WCTT = transmissionTime

				if time * timeResolution > framelet.releaseTime + framelet.stream.deadline:
					framelet.stream.deadline
					time * timeResolution
					misses.add(framelet)

		return misses


@dataclass
class InputPort:
	name: str

	def __hash__(self: InputPort) -> int:
		return hash(self.name)

	def __eq__(self: InputPort, other: InputPort) -> bool:
		return self.name == other.name


@dataclass
class Link:
	src: Device
	dest: Device

	def __hash__(self: Link) -> int:
		return hash((self.src, self.dest))

	def __eq__(self: Link, other: object) -> bool:
		if isinstance(other, Link):
			return self.src is other.src and self.dest is other.dest

		return False


@dataclass
class StreamSolution:
	stream: Stream
	routes: list[Route]


@dataclass
class Solution:
	streamSolutions: list[StreamSolution]

	def printSolution(self: Solution) -> None:
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

	def matchRedudancy(self: Solution) -> None:
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
	links: list[Link]

	def __hash__(self: Route) -> int:
		return hash(tuple(self.links))

	def __eq__(self: Route, other: object) -> bool:
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

	def __hash__(self: Stream) -> int:
		return hash(self.id + hash(self.instance))

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
	add TTL ?

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
	src : EndSystem
		a source device
	dest : EndSystem
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
	WCTT : int
		Worst-case transmission time detected while simulating
	"""

	id: str
	src: EndSystem
	dest: EndSystem
	size: int
	period: int
	deadline: int
	rl: int
	instances: list[StreamInstance] = field(default_factory=list)
	routes: dict[int, list[Device]] = field(default_factory=list)
	WCTT: int = 0

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
