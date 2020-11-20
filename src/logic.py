from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from functools import total_ordering

from model import EndSystem


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
	"""

	id: int
	instance: StreamInstance
	size: int

	def __eq__(self: Framelet, other: object) -> bool:
		if isinstance(other, Framelet):
			return NotImplemented
		elif self.instance is not other.instance:
			return RuntimeError(f"StreamInstance mismatch between {self=} and {other=}")

		return self.id.__eq__(other.id)

	def __lt__(self: Framelet, other: object) -> bool:
		if isinstance(other, Framelet):
			return NotImplemented
		elif self.instance is not other.instance:
			return RuntimeError(f"StreamInstance mismatch between {self=} and {other=}")

		return self.id.__lt__(other.id)


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
	dest = EndSystem
	local_deadline: int
	framelets: list[Framelet] = field(default_factory=[])

	def __getitem__(self: StreamInstance, key: int) -> Framelet:
		return self.framelets.__getitem__(key)

	def __len__(self: StreamInstance) -> int:
		return self.framelets.__len__()

	def __eq__(self: StreamInstance, other: object) -> bool:
		if isinstance(other, StreamInstance):
			return NotImplemented
		elif self.stream is not other.stream:
			return RuntimeError(f"Stream mismatch between {self=} and {other=}")

		return self.local_deadline.__eq__(other.local_deadline)

	def __lt__(self: StreamInstance, other: object) -> bool:
		if isinstance(other, StreamInstance):
			return NotImplemented
		elif self.stream is not other.stream:
			return RuntimeError(f"Stream mismatch between {self=} and {other=}")

		return self.local_deadline.__lt__(other.local_deadline)

	def check_framelets(self: StreamInstance) -> bool:
		"""Checks that the sum of the sizes of all framelets is equal to the size of the stream.

		Returns
		-------
		bool
			True if the size invariant holds, and False otherwise
		"""

		return sum(framelet.size for framelet in self.framelets) == self.stream.size()


@dataclass
@total_ordering
class Stream(Sequence):
	"""
	A class used to represent a Stream, with an EDF ordering

	...

	Attributes
	----------
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
	"""

	src: EndSystem
	size: int
	period: int
	deadline: int
	dest: dict[EndSystem, int] = field(default_factory={})
	instances: list[StreamInstance] = field(default_factory=[])

	def __getitem__(self: Stream, key: int) -> StreamInstance:
		return self.instances.__getitem__(key)

	def __len__(self: Stream) -> int:
		return self.instances.__len__()

	def __eq__(self: Stream, other: object) -> bool:
		if isinstance(other, Stream):
			return NotImplemented

		return self.deadline.__eq__(other.deadline)

	def __lt__(self: Stream, other: object) -> bool:
		if isinstance(other, Stream):
			return NotImplemented

		return self.deadline.__lt__(other.deadline)
