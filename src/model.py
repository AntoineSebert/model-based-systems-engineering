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


@dataclass(eq=False)
class EndSystem(Device):
	remainder: int = 0
	ingress: list['Framelet'] = field(default_factory=list)
