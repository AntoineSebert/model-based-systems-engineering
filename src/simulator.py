import logging

from model import Switch, EndSystem, Results, Stream

from networkx import DiGraph  # type: ignore


def _events(logger, iteration: int, timeResolution: int, network: DiGraph, streams: set[Stream]) -> set['Framelet']:
	misses = set()

	# Check if new framelets should be added to EndSystem queue for emission
	for endSystem in filter(lambda n: isinstance(n, EndSystem), network.nodes):
		endSystem.enqueueStreams(network, iteration, timeResolution)

	# Go through all endsystem and switches in network and emit from egress queue
	for device in filter(lambda n: isinstance(n, EndSystem) or isinstance(n, Switch), network.nodes):
		device.emit(network, timeResolution)


	for device in filter(lambda n: isinstance(n, EndSystem) or isinstance(n, Switch), network.nodes):
		misses |= device.receive(network, iteration, timeResolution)

	for stream in misses:
		logger.warning(f"Missed deadline for {stream.id} at time {iteration*timeResolution}")

	return misses


# resources in OneDrive slides
def simulate(network: DiGraph, streams: set[Stream], time_limit: int, stop_on_miss: bool) -> Results:
	logger = logging.getLogger()
	timeResolution = 5 # Number of microseconds simulated in a single iteration
	iteration: int = 0
	loop_cond = (lambda t, tl: t < tl) if 0 < time_limit else (lambda tl, t: True)
	misses: set[Stream] = set()
	totalMisses = 0
	while loop_cond(iteration, time_limit):
		# print("Time({})".format(iteration))

		misses = _events(logger, iteration, timeResolution, network, streams)
		totalMisses += len(misses)
		if len(misses) != 0 and stop_on_miss:
			break

		misses.clear()

		iteration += 1

	print("Missed a total of {} deadlines when running for {} milliseconds".format(totalMisses, iteration*timeResolution/1000.0))

	wctt_sum = 0
	wctts = []

	for stream in streams:
		print("Stream{} WCTT: {} microseconds".format(stream.id, stream.WCTT))
		wctt_sum += stream.WCTT
		wctts.append(stream.WCTT)
	print()
	print("Average WCTT: {} microseconds".format(round(wctt_sum / len(streams), 2)))
	print("Worst transmission time: {} microseconds".format(max(wctts)))
	logger.info("done.")

	return Results(network, streams, {})
