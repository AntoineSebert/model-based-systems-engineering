import logging

from model import Switch, Device, EndSystem, Results, Stream

from networkx import DiGraph  # type: ignore


def _events(logger, iteration: int, timeResolution: int, network: DiGraph, streams: set[Stream],
	emitters: set[EndSystem], receivers: set[Device]) -> set['Framelet']:

	misses = set()

	# Check if new framelets should be added to EndSystem queue for emission
	for device in emitters:
		device.enqueueStreams(network, iteration, timeResolution)

	# Go through all endsystem and switches in network and emit from egress queue
	for device in emitters:
		device.emit(network, timeResolution)

	for device in receivers:
		misses |= device.receive(network, iteration, timeResolution)

	for stream in misses:
		logger.warning(f"Missed deadline for {stream.id} at time {iteration*timeResolution}")

	return misses


def simulate(network: DiGraph, streams: set[Stream], time_limit: int, stop_on_miss: bool) -> Results:
	logger = logging.getLogger()
	timeResolution = 8 # Number of microseconds simulated in a single iteration
	iteration: int = 0
	loop_cond = (lambda t, tl: t < tl) if 0 < time_limit else (lambda tl, t: True)
	misses: set[Stream] = set()
	totalMisses = 0

	emitters: set[EndSystem] = {stream.src for stream in streams}
	receivers: set[Device] = {stream.dest for stream in streams}

	while loop_cond(iteration, time_limit):
		misses = _events(logger, iteration, timeResolution, network, streams, emitters, receivers)
		totalMisses += len(misses)

		if len(misses) != 0 and stop_on_miss:
			break

		misses.clear()

		iteration += 1

	wctt_sum = 0
	wctts = []

	for stream in streams:
		wctt_sum += stream.WCTT
		wctts.append(stream.WCTT)

	logger.info("done.")

	return Results(network, streams, {})
