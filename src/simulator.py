import logging

from model import Device, EndSystem, Framelet, Scheduling, Solution, Stream

from networkx import DiGraph  # type: ignore

from queue import PriorityQueue

def _events(iteration: int, timeResolution: int, network: DiGraph, streams: set[Stream], scheduling: Scheduling,
	emitters: set[Device], receivers: set[Device]) -> set[Framelet]:
	logger = logging.getLogger()
	misses = set()

	# Check if new framelets should be added to EndSystem queue for emission
	for device in filter(lambda e: isinstance(e, EndSystem), emitters):
		device.enqueueStreams(iteration, timeResolution)

	# Go through all endsystem and switches in network and emit from egress queue
	for device in emitters:
		device.emit(network, timeResolution)

	for device in receivers:
		misses |= device.receive(iteration, timeResolution)

	for stream in misses:
		logger.warning(f"Missed deadline for {stream.id} at time {iteration*timeResolution}")

	return misses


def simulate(network: DiGraph, streams: set[Stream], scheduling: Scheduling, emitters: set[Device],
	receivers: set[Device], time_limit: int, stop_on_miss: bool) -> Solution:
	logger = logging.getLogger()
	iteration: int = 0
	loop_cond = (lambda t, tl: t < tl) if time_limit > 0 else (lambda tl, t: True)
	misses: set[Stream] = set()
	totalMisses = 0

	while loop_cond(iteration, time_limit):
		misses = _events(iteration, timeResolution, network, streams, scheduling, emitters, receivers)

		if misses:
			totalMisses += len(misses)
			misses.clear()

			if stop_on_miss:
				break

		# Extract the currently youngest device in terms of simulator age
		# Store this time as the simulators overall guarenteed time simulated so far
		simulator_age_current, currentDevice = deviceQueue.get()
		if simulator_age_current > simulator_age_last:
			for device in network.nodes:
				device.receive()
		simulator_age_last = simulator_age_current
		# misses.clear()

	logger.info("done.")

	return Solution(network, streams, {})
