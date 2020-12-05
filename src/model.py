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
	localTime: float = 0.0

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
		if not self.egress.empty():
			frame = self.egress.get()
			nextStep = next(link for link in frame.route.links if link.src == self)
			speed = network.get_edge_data(nextStep.src, nextStep.dest)['speed']
			receiver = next(device for device in network._node if device == nextStep.dest)

			# advance time for this device and the frame sent
			self.localTime += 64.0 / speed
			frame.localTime = self.localTime
			receiver.ingress.put(frame) # Send framelet
		else:
			self.localTime += 64 / 12.5

		logging.info(f"Swtich {self.name} emitted framelet")


@dataclass(eq=False)
class Switch(Device):
	def receive(self: Switch) -> set[Stream]:
		misses: set[Stream] = set()

		for framelet in self.ingress:
			logging.info(f"Switch {self.name} received framelet")
			self.egress.put(framelet)  # Queue instead

		return misses


@dataclass(eq=False)
class EndSystem(Device):
	streams: list[Stream] = field(default_factory=list)

	def receive(self: EndSystem) -> set[Stream]:
		misses: set[Stream] = set()

		for framelet in self.ingress:
			logging.info(f"EndSystem {self.name} received framelet from")

			if self.name != framelet.route.links[-1].dest:
				self.egress.put(framelet)  # Queue instead
			else:  # Check if deadline is passed for frame
				if framelet.stream_instance.stream.WCTT < framelet.localTime - framelet.stream_instance.release_time:
					framelet.stream_instance.stream.WCTT = framelet.localTime - framelet.stream_instance.release_time

				if framelet.localTime > framelet.stream_instance.local_deadline:
					misses.add(framelet.stream_instance.stream)

		return misses


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
	release_time: int
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

	def create_framelets(self: StreamInstance):
		# This puts the frames in order by a route basis. Could be changed to put frames in queue on an index basis
		max_framelet_size: int = 64

		for route in self.stream.routes:
			complete = int(self.stream.size / max_framelet_size)
			self.framelets.extend(Framelet(i, self, max_framelet_size, route) for i in range(complete))

			if (rest := self.stream.size % max_framelet_size) != 0:
				self.framelets.append(Framelet(complete, self, rest, route))


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
	routes : dict[float, list[list[Device]]]
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

	def redundancyCheck(self: Solution) -> dict[Stream, bool]:
		'''

		Parameters
		----------
		solution

		Returns
		-------
		A list of stream solutions and a bool for each denoting whether network topology supports the required redundancy level.
		True if so, False if no.
		'''

		redundant = [[True, stream] for stream in solution.stream]

		for index, stream in enumerate(solution.stream):
			unique_links = set([link for route in stream.routes for link in route.links])
			fault_tolerance = int(stream.rl) - 1

			if fault_tolerance > 0:
				link_combinations = combinations(unique_links, fault_tolerance)

				for comb in link_combinations:
					if all(bool(set(comb) & set(route.links)) for route in stream.routes):
						redundant[index][0] = False

		return redundant

	def redundancySatisfiedRatio(solution: Solution) -> float:
		redundant = redundancyCheck(solution)

		numOfSolutions = len(redundant)
		numOfSatisfied = 0.0

		for sol in redundant:
			if sol[0]:
				numOfSatisfied += 1

		ratio = (numOfSatisfied / numOfSolutions) * 100 #percentage of satisfied redundancy levels
		print("ratio: ", ratio)
		return ratio

	def getCostFromSwitchDegree(degree: int) -> int:
		cost = 0

		#cost defined by automotive example.xlsx (multiplied by 2 to avoid using floats)

		if degree > 8:
			cost = 50 * (degree - 8) #penalty for exceeding number of allowed external ports
		elif degree == 2:
			cost = 2
		elif degree == 3:
			cost = 3
		elif degree == 4:
			cost = 5
		elif degree == 5:
			cost = 8
		elif degree == 6:
			cost = 9
		elif degree == 8:
			cost = 11
		else:
			print("SWITCH HAS DEGREE ", degree, " which is not allowed")
			cost = 500

		return cost

	def monetaryCost(self: Solution) -> int:
		#nextStep = next(device for device in network. if link.src == self.name)
		cost = 0

		for device in self.network.nodes:
			if isinstance(device, Switch):
				degree = self.network.degree(device)
				currCost = getCostFromSwitchDegree(degree)
				print("Switch ", device.name, " has degree ", degree, " with cost ", currCost)
				cost += currCost

		return cost


"""
The structure is:
- key: emission time, hyperperiod-wise
- value : dict
	- key : emitting device
	- value : set of streams to emit by said device
"""
Scheduling = dict[int, dict[EndSystem, set[StreamInstance]]]
