from dataclasses import dataclass
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
	speed: float = 1.0


@dataclass(eq=False)
class EndSystem(Device):
	pass