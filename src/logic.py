from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from functools import total_ordering
from typing import Union

from model import EndSystem

from networkx import DiGraph  # type: ignore


@dataclass
class Route:
	subgraph: DiGraph

	def check(self: Route) -> None:
		# check if subgraph only is a sequence of nodes, with EndSystem as src and dest
		pass

	def transmission_time(self: Route, size: int) -> int:
		return sum(-(-size // speed) for u, v, speed in self.subgraph.edges(data="speed"))


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
	instance: StreamInstance
	size: int

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
	dest: EndSystem
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
	dest : dict[EndSystem, int]
		the destination devices, with devices as keys and redundancy levels as values
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
	src: EndSystem
	dest: EndSystem
	size: int
	period: int
	deadline: int
	rl: int
	instances: list[StreamInstance] = field(default_factory=list)

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
	routes : dict[Stream, set[Route]]
		a dictionary of streams as keys and set of routes as values
	"""

	network: DiGraph
	streams: set[Stream] = field(default_factory=set)
	routes: dict[Stream, set[Route]] = field(default_factory=dict)
