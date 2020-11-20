import logging

from logic import Solution, Stream

from networkx import DiGraph  # type: ignore


# resources in OneDrive slides
def simulate(network: DiGraph, streams: set[Stream]) -> Solution:
	logger = logging.getLogger()

	while True:
		break

	logger.info("done.")

	return Solution(network, streams, {})
