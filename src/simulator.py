import logging

from model import Device, EndSystem, Framelet, Scheduling, Solution, Stream, StreamInstance

from networkx import DiGraph  # type: ignore

from queue import PriorityQueue


def simulate(network: DiGraph, streams: set[Stream], scheduling: Scheduling, emitters: set[Device],
	receivers: set[Device], time_limit: int, stop_on_miss: bool) -> Solution:
	logger = logging.getLogger()
	iteration: int = 0
	loop_cond = (lambda t, tl: t < tl) if time_limit > 0 else (lambda tl, t: True)
	misses: set[Stream] = set()
	totalMisses = 0
	simulator_age_current = 0
	simulator_age_last = simulator_age_current

	deviceQueue = PriorityQueue()
	for device in network.nodes:
		deviceQueue.put((device.localTime, device))

	streamScheduler = PriorityQueue()
	for stream in streams:
		stream_instance = StreamInstance(stream, simulator_age_current, 0 * stream.period + stream.deadline)
		stream_instance.create_framelets()
		streamScheduler.put((stream_instance.release_time, stream_instance))

	simulator_age_current, currentDevice = deviceQueue.get()

	while loop_cond(iteration, time_limit):
		while True:
			release_time, stream_instance = streamScheduler.get()
			if release_time > simulator_age_current:
				# Put stream instance back. We cannot enqueue it yet
				streamScheduler.put((release_time, stream_instance))
				break

			# Enqueue stream framelets at device
			for framelet in stream_instance.framelets:
				stream_instance.stream.src.egress.put(framelet)

			# Create entirely new stream instance
			stream_instance = StreamInstance(
				stream_instance.stream,
				stream_instance.release_time + stream_instance.stream.period,
				stream_instance.release_time + stream_instance.stream.period + stream_instance.stream.deadline
			)
			stream_instance.create_framelets()
			streamScheduler.put((stream_instance.release_time, stream_instance))

		# Perform receive and emit for the device
		currentDevice.emit(network)  # Emit next framelet

		if misses and stop_on_miss:
			break

		# Put the device back on the queue with its updated age
		deviceQueue.put((currentDevice.localTime, currentDevice))

		# Extract the currently youngest device in terms of simulator age
		# Store this time as the simulators overall guarenteed time simulated so far
		simulator_age_current, currentDevice = deviceQueue.get()
		if simulator_age_current > simulator_age_last:
			for device in network.nodes:
				device.receive()
		simulator_age_last = simulator_age_current

		iteration += 1

	logger.info("done.")

	return Solution(network, streams, {})
