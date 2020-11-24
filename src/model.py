from __future__ import annotations

from dataclasses import dataclass, field
from queue import PriorityQueue


@dataclass
class Device:
	name: str

	def __hash__(self):
		return hash(self.name)

	def __eq__(self, other):
		if isinstance(other, Device):
			return self.name == other.name
		return False


@dataclass(eq=False)
class Switch(Device):
	queue: PriorityQueue = PriorityQueue()
	speed: float = 1.0

	def emit(self, time: int) -> None:
		pass

	def receive(self, time: int) -> list['Stream']:
		misses = {}
		"""
		for framelet in ingress:
			logging.info(f"EndSystem {self.name} received framelet from {framelet.to_string()}")

			if time < framelet.instance.local_deadline:
				misses.add(framelet.instance.stream)
		"""

		return misses


@dataclass(eq=False)
class EndSystem(Device):
	remainder: int = 0
	ingress: list['Framelet'] = field(default_factory=list)

	def emit(self, time: int) -> None:
		pass

	def receive(self: EndSystem, time: int) -> set['Stream']:
		misses = {}

		for framelet in self.ingress:
			logging.info(f"EndSystem {self.name} received framelet from {framelet.to_string()}")

			if time < framelet.instance.local_deadline:
				misses.add(framelet.instance.stream)

		self.ingress.clear()

		return misses
