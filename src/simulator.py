import logging

from model import Switch, EndSystem, Device, Results, Stream, StreamInstance

from networkx import DiGraph  # type: ignore

from queue import PriorityQueue

from copy import deepcopy


# resources in OneDrive slides
def simulate(network: DiGraph, streams: set[Stream], time_limit: int, stop_on_miss: bool) -> Results:
	logger = logging.getLogger()
	iteration: int = 0
	simulator_age_current = 0
	simulator_age_last = simulator_age_current

	deviceQueue = PriorityQueue()
	for device in network.nodes:
		deviceQueue.put((device.localTime, device))

	streamScheduler = PriorityQueue()
	for stream in streams:
		stream_instance = StreamInstance(stream, 0, simulator_age_current,
										 0 * int(stream.period) + int(stream.deadline))
		stream_instance.create_framelets()
		streamScheduler.put((stream_instance.release_time, stream_instance))

	misses: set[Stream] = set()
	totalMisses = 0

	loop_cond = (lambda t, tl: t < tl) if 0 < time_limit else (lambda tl, t: True)
	simulator_age_current, currentDevice = deviceQueue.get()
	while loop_cond(simulator_age_last, time_limit):
		# print(simulator_age_current)
		# Check if new stream instances should be scheduled
		while True:
			release_time, stream_instance = streamScheduler.get()
			if release_time > simulator_age_current:
				# Put stream instance back. We cannot enqueue it yet
				streamScheduler.put((release_time, stream_instance))
				break
			# Enqueue stream framelets at device
			for framelet in stream_instance.framelets:
				stream_instance.stream.device.egress_main.put(framelet)

			# Create entirely new stream instance
			stream_instance = StreamInstance(stream_instance.stream,
												stream_instance.instance + 1,
												stream_instance.release_time + int(stream_instance.stream.period),
												stream_instance.release_time + int(stream_instance.stream.period) + int(stream_instance.stream.deadline))
			stream_instance.create_framelets()
			streamScheduler.put((stream_instance.release_time, stream_instance))

		# Perform receive and emit for the device
		currentDevice.emit(network)  # Emit next framelet

		totalMisses += len(misses)
		if len(misses) != 0 and stop_on_miss:
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
		# misses.clear()

	print("Simulated for {} microseconds".format(simulator_age_last))
	# print("Missed a total of {} deadlines when running for {} milliseconds".format(totalMisses, iteration*timeResolution/1000.0))
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
