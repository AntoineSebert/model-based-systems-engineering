import logging

from logic import Results, Stream

from model import Switch, EndSystem

from networkx import DiGraph  # type: ignore


def _events(logger, time: int, network: DiGraph, streams: set[Stream]) -> set[Stream]:
	misses = set()

	# Check if new framelets should be added to EndSystem queue for emission
	for endSystem in filter(lambda n: isinstance(n, EndSystem), network.nodes):
		endSystem.enqueueStreams(network, time)

	# Go through all end in network and emit from egress queue
	for device in filter(lambda n: isinstance(n, EndSystem) or isinstance(n, Switch), network.nodes):
		device.emit(time, network)

	for device in filter(lambda n: isinstance(n, EndSystem) or isinstance(n, Switch), network.nodes):
		misses |= device.receive(time, network)

	for stream in misses:
		logger.warning(f"Missed deadline for {stream.id} at {time}")

	return misses


# resources in OneDrive slides
def simulate(network: DiGraph, streams: set[Stream], time_limit: int, stop_on_miss: bool) -> Results:
	logger = logging.getLogger()

	time: int = 0
	loop_cond = (lambda t, tl: t < tl) if 0 < time_limit else (lambda tl, t: True)
	misses: set[Stream] = set()

	while loop_cond(time, time_limit):
		if not time % 500:
			print("Time({})".format(time))

		misses = _events(logger, time, network, streams)

		if len(misses) != 0 and stop_on_miss:
			break

		misses.clear()

		time += 1

	logger.info("done.")

	return Results(network, streams, {})
