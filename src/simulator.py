import logging

from model import Device, EndSystem, Framelet, Solution, Stream, StreamInstance

from networkx import DiGraph  # type: ignore

from queue import PriorityQueue

from typing import Optional


def enqueue_streams(sched_current, simulator_age):
	for stream in sched_current[1]:
		instance = StreamInstance(stream, simulator_age, simulator_age + stream.deadline)
		stream.instances.append(instance)

		# Enqueue stream framelets at device
		for framelet in instance.create_framelets():
			stream.src.egress.put(framelet)


def simulate(network: DiGraph, streams: set[Stream], scheduling: dict[int, set[Stream]], emitters: set[Device],
	receivers: set[Device], time_limit: int, stop_on_miss: bool, hyperperiod: int) -> Solution:
	logger = logging.getLogger()
	iteration: int = 0
	misses: set[Stream] = set()
	simulator_age_current = 0.0
	simulator_age_last = simulator_age_current
	scheduler_it = iter(scheduling.items())

	# Check edge case for all stream periods being equal
	periods_equal = True
	period = 0
	period = next(scheduler_it)[0]
	try:
		for sched in scheduler_it:
			if sched[0] != period:
				periods_equal = False
				break
	except:
		pass

	scheduler_it = iter(scheduling.items())
	sched_current = next(scheduler_it)

	deviceQueue = PriorityQueue()
	for device in network.nodes:
		deviceQueue.put((device.localTime, device))

	simulator_age_current, currentDevice = deviceQueue.get()

	loop_cond = (lambda t, tl: t < tl) if time_limit > 0 else (lambda tl, t: True)

	while loop_cond(iteration, time_limit):
		if periods_equal and simulator_age_current >= period:
			enqueue_streams(sched_current, simulator_age_current)
			period += list(sched_current[1])[0].period
		elif not periods_equal and sched_current[0] <= simulator_age_current % hyperperiod:
			enqueue_streams(sched_current, simulator_age_current)
			try:
				sched_current = next(scheduler_it)
			except StopIteration:
				scheduler_it = iter(scheduling.items())
				sched_current = next(scheduler_it)

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

	return Solution(network, streams), simulator_age_current
