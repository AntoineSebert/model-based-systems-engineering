import logging

from logic import Solution, Stream

from networkx import DiGraph  # type: ignore


# resources in OneDrive slides
def simulate(network: DiGraph, streams: set[Stream], time_limit: int, stop_on_miss: bool) -> Solution:
	logger = logging.getLogger()

	print(time_limit, stop_on_miss)

	while True:
		break

	logger.info("done.")

	return Solution(network, streams, {})
