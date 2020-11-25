from __future__ import annotations

import logging
from dataclasses import dataclass, field
from queue import PriorityQueue
from networkx import DiGraph
from logic import Stream

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

	def emit(self: Switch, time: int) -> None:
		pass

	def receive(self: Switch, time: int) -> set['Stream']:
		misses: set['Stream'] = set()
		temp: PriorityQueue = PriorityQueue()

		while not self.queue.empty():
			priority, framelet = self.queue.get()
			logging.info(f"Switch {self.name} received framelet from {framelet.to_string()}")

			if time < framelet.instance.local_deadline:
				misses.add(framelet.instance.stream)

			self.temp.put((priority, framelet))

		self.queue = temp

		return misses


@dataclass(eq=False)
class EndSystem(Device):
	streams: list[Stream] = field(default_factory=list)
	remainder: int = 0
	ingress: list['Framelet'] = field(default_factory=list)  # replace by dict(time, frames)
	
	def emit(self: EndSystem, time: int, network: DiGraph, stream: Stream) -> None:

		#todo: check deadline?

		for framelet in self.ingress:
			neighbors = network.edges(self)

			for n in neighbors:
				pass
				#print("neigh: ", n, "\n\n\n\n")

		logging.info(f"EndSystem {self.name} emitted framelet")


	def receive(self: EndSystem, time: int) -> set['Stream']:
		misses: set['Stream'] = set()

		for framelet in self.ingress:
			logging.info(f"EndSystem {self.name} received framelet from")

			#if time < framelet.instance.local_deadline:
			#	misses.add(framelet.instance.stream)

		self.ingress.clear()

		return misses
