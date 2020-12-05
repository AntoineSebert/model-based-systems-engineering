from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from functools import total_ordering
from queue import PriorityQueue
from typing import overload

from networkx import DiGraph  # type: ignore

@total_ordering
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
		else:
			return NotImplemented

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
            frame.localTime = self.localTime
            receiver.ingress.put(frame) # Send framelet
        else:
            self.localTime += 64 / 12.5

        logging.info(f"Swtich {self.name} emitted framelet")


@dataclass(eq=False)
class Switch(Device):
	def receive(self: Switch, time: int, timeResolution: int) -> set[Stream]:
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

			if self.name != framelet.route.links[-1].dest:
				self.egress.put(framelet)
			else:
				transmissionTime = time * timeResolution - framelet.releaseTime

@dataclass
class Link:
    src: str
    dest: str

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
	routes: dict[float, list[list[Device]]] = field(default_factory=dict)
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


"""
The structure is:
- key: emission time, hyperperiod-wise
- value : dict
	- key : emitting device
	- value : set of streams to emit by said device
"""
Scheduling = dict[int, dict[EndSystem, set[StreamInstance]]]
