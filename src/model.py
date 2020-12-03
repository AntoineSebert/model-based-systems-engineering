from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from functools import total_ordering
from queue import PriorityQueue
from typing import overload

from networkx import DiGraph  # type: ignore


@dataclass
class Device:
	name: str
	ingress: list[Framelet] = field(default_factory=list)
	egress: PriorityQueue[Framelet] = field(default_factory=PriorityQueue)

	def __hash__(self: Device) -> int:
		return hash(self.name)

	def __eq__(self: Device, other: object) -> bool:
		if isinstance(other, Device):
			return self.name == other.name
		return False

	def emit(self: Device, network: DiGraph, timeResolution: int) -> None:
		if not self.egress.empty():
			iterationTime = timeResolution
			inIteration = 0

			# figure out what does this bulk do ?
			while (inIteration <= iterationTime):
				if self.remainingSize <= 0:
					self.currentFrame = self.egress.get()
					self.remainingSize = self.currentFrame.size
					nextStep = next(link for link in self.currentFrame.route.links if link.src == self.name)
					self.currentSpeed = network.get_edge_data(Device(nextStep.src), Device(nextStep.dest))['speed']
					self.currentReceiver = next(device for device in network._node if device == Device(nextStep.dest))

				sendable = min(self.remainingSize, max((iterationTime - inIteration) * self.currentSpeed, 1.0))

				if inIteration + sendable / self.currentSpeed > iterationTime:
					break
				self.remainingSize -= sendable

				if self.remainingSize <= 0:
					self.currentReceiver.ingress.append(self.currentFrame)
					self.currentFrame = None
				inIteration += (float(sendable) / self.currentSpeed)

			logging.info(f"Swtich {self.name} emitted framelet")


@dataclass(eq=False)
class Switch(Device):
	def receive(self: Switch, network: DiGraph, time: int, timeResolution: int) -> set[Stream]:
		misses: set[Stream] = set()

		for framelet in self.ingress:
			logging.info(f"Switch {self.name} received framelet")
			self.egress.put(framelet)

			if framelet.instance.local_deadline < time:
				misses.add(framelet.instance.stream)

		return misses


@dataclass(eq=False)
class EndSystem(Device):
	streams: list[Stream] = field(default_factory=list)

	def enqueueStreams(self: EndSystem, network: DiGraph, iteration: int, timeResolution: int) -> None:
		index = 0
		for stream in filter(lambda n: not (iteration * timeResolution % n.period), self.streams):
			for route in stream.routes:
				index = index + 1
				self.egress.put(Framelet(index, stream.instance, stream.size, route))

	def receive(self: EndSystem, network: DiGraph, time: int, timeResolution: int) -> set[Framelet]:
		misses: set[Framelet] = set()

		for framelet in self.ingress:
			logging.info(f"EndSystem {self.name} received framelet from")

			if self.name != framelet.route.links[-1].dest:
				self.egress.put(framelet)
			else:
				transmissionTime = time * timeResolution - framelet.releaseTime

				if framelet.stream.WCTT < transmissionTime:
					framelet.stream.WCTT = transmissionTime

			if framelet.instance.local_deadline < time:
				misses.add(framelet.instance.stream)

		return misses

		logging.info(f"EndSystem {self.name} emitted framelet")


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
	route : list[Device]
		The ordered list of devices the instance has to go through, without counting the emitting device

	Methods
	-------
	to_string()
		Returns a short string description of the Framelet
	"""

	id: int
	instance: StreamInstance
	size: int
	route: list[Device]

	def __eq__(self: Framelet, other: object) -> bool:
		if isinstance(other, Framelet):
			return self.instance.stream.rl.__eq__(other.instance.stream.rl)
		else:
			return NotImplemented

	def __lt__(self: Framelet, other: object) -> bool:
		if isinstance(other, Framelet):
			return self.instance.stream.rl.__lt__(other.instance.stream.rl)
		else:
			return NotImplemented

	def __hash__(self: Framelet) -> int:
		return hash(self.id + self.instance.__hash__())

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

		src_dest = self.instance.stream.src.name + "-" + self.instance.stream.dest.name

		return f"{self.instance.stream.id}[{src_dest}]/{self.instance.local_deadline}/{self.id}:{self.size}"


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
	local_deadline: int
	framelets: list[Framelet] = field(default_factory=list)

	@overload
	def __getitem__(self: StreamInstance, key: int) -> Framelet:
		return self.framelets.__getitem__(key)

	@overload
	def __getitem__(self: StreamInstance, key: slice) -> Sequence[Framelet]:
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

	def __hash__(self: StreamInstance) -> int:
		return hash(self.stream.id.__hash__() + self.local_deadline)

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
	routes : dict[int, list[Device]]
		a dict of time cost as key and associated routes as values
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
	routes: dict[int, list[Device]] = field(default_factory=dict)
	WCTT: int = 0

	def __hash__(self: Stream) -> int:
		return hash(self.id)

	@overload
	def __getitem__(self: Stream, key: int) -> StreamInstance:
		return self.instances.__getitem__(key)

	@overload
	def __getitem__(self: Stream, key: slice) -> Sequence[StreamInstance]:
		return self.instances.__getitem__(key)

	def __len__(self: Stream) -> int:
		return self.instances.__len__()

	def __eq__(self: Stream, other: object) -> bool:
		if isinstance(other, Stream):
			return self is other

		return NotImplemented

	def __lt__(self: Stream, other: object) -> bool:
		if isinstance(other, Stream):
			return self.deadline.__lt__(other.deadline)

		return NotImplemented


@dataclass
class Solution:
	"""
	A class used to represent a Solution

	...

	Attributes
	----------
	network : DiGraph
		a
	streams : set[Stream]
		a set of streams
	routes : dict[Stream, set[list[Device]]]
		a dictionary of streams as keys and set of routes as values
	"""

	network: DiGraph
	streams: set[Stream] = field(default_factory=set)
	routes: dict[Stream, set[list[Device]]] = field(default_factory=dict)

	def transmission_time(self: Solution) -> tuple[list[int], int]:
		wctts = [stream.WCTT for stream in self.streams]
		return wctts, sum(wctts)
