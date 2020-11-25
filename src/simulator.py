import logging

from logic import Results, Stream

from model import Switch, EndSystem

from networkx import DiGraph  # type: ignore


def _events(logger, time: int, network: DiGraph, streams: set[Stream]) -> set[Stream]:
	misses = set()

	# Check if new framelets should be added to EndSystem queue for emission
	for device in network.nodes:
		if isinstance(device, EndSystem):
			device.enqueueStreams(network, time)
	# Go through all devices in network and emit from egress queue
	for endsys in network.nodes:
		if isinstance(endsys, EndSystem):
			endsys.emit(time, network)

	# For all switches, receive framelets on ingress and add to egress queue
	for switch in filter(lambda n: isinstance(n, Switch), network.nodes):
		misses |= switch.receive(time)


	for switch in filter(lambda n: isinstance(n, Switch), network.nodes):
		switch.emit(time)

	# for stream in streams:
	# 	misses |= stream.src.receive(time)

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
		#print(time)

		misses = _events(logger, time, network, streams)

		if len(misses) != 0 and stop_on_miss:
			break

		misses.clear()

		time += 1

	logger.info("done.")

	return Results(network, streams, {})
