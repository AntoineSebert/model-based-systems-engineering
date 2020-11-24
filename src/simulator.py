import logging

from logic import Solution, Stream

from model import Switch

from networkx import DiGraph  # type: ignore


def _events(time: int, network: DiGraph, streams: set[Stream]) -> list[Stream]:
	misses = []

	for stream in streams:
		stream.src.emit(time)

	for switch in filter(lambda n: isinstance(n, Switch), network.nodes):
		misses += switch.receive(time)

	for switch in filter(lambda n: isinstance(n, Switch), network.nodes):
		switch.emit(time)

	for stream in streams:
		misses += stream.src.receive(time)

	return misses


# resources in OneDrive slides
def simulate(network: DiGraph, streams: set[Stream], time_limit: int, stop_on_miss: bool) -> Solution:
	logger = logging.getLogger()

	time: int = 0
	loop_cond = (lambda tl, t: tl < t) if 0 < time_limit else (lambda tl, t: True)
	misses: list[Stream] = []

	while loop_cond(time_limit, time):
		misses = _events(time, network, streams)

		for stream in misses.items():
			logger.warning(f"Missed deadline for {stream=} at {time}")

		if len(misses) != 0 and stop_on_miss:
			break

		misses.clear()

		time += 1

	logger.info("done.")

	return Solution(network, streams, {})
