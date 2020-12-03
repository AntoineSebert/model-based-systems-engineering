import logging

from model import Switch, EndSystem, Device, Results, Stream, StreamInstance

from networkx import DiGraph  # type: ignore

from queue import PriorityQueue

from copy import deepcopy


def enqueue_stream_instance(network: DiGraph, stream: Stream, device: EndSystem):
    pass


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
        logger.warning(f"Missed deadline for {stream.id} at time {iteration * timeResolution}")

    return misses


# resources in OneDrive slides
def simulate(network: DiGraph, streams: set[Stream], time_limit: int, stop_on_miss: bool) -> Results:
    logger = logging.getLogger()
    iteration: int = 0
    simulator_age = 0

    deviceQueue = PriorityQueue()
    for device in network.nodes:
        deviceQueue.put((device.localTime, device))

    streamScheduler = PriorityQueue()
    for stream in streams:
        stream_instance = StreamInstance(stream, stream.dest, 0, simulator_age,
                                         0 * int(stream.period) + int(stream.deadline))
        stream_instance.create_framelets()
        streamScheduler.put((stream_instance.release_time, stream_instance))

    misses: set[Stream] = set()
    totalMisses = 0

    loop_cond = (lambda t, tl: t < tl) if 0 < time_limit else (lambda tl, t: True)

    while loop_cond(iteration, time_limit):
        # print("Time({})".format(iteration))
        # Check if new stream instances should be scheduled

        while True:
            release_time, stream_instance = streamScheduler.get()
            if release_time > simulator_age:
                # Put stream instance back. We cannot enqueue it yet
                streamScheduler.put((release_time, stream_instance))
                break
            # Enqueue stream framelets at device
            for framelet in stream_instance.framelets:
                stream_instance.stream.device.egress_main.put(framelet)

            # Create entirely new stream instance
            stream_instance = StreamInstance(stream_instance.stream,
                                                stream_instance.dest,
                                                stream_instance.instance + 1,
                                                stream_instance.release_time + int(stream_instance.stream.period),
                                                stream_instance.release_time + int(stream_instance.stream.period) + int(stream_instance.stream.deadline))
            stream_instance.create_framelets()
            streamScheduler.put((stream_instance.release_time, stream_instance))

        # Extract the currently youngest device in terms of simulator age
        # Store this time as the simulators overall guarenteed time simulated so far
        simulator_age, currentDevice = deviceQueue.get()

        # Perform receive and emit for the device
        misses = currentDevice.receive()  # Load everything in ingress
        currentDevice.emit(network)  # Emit next framelet
        totalMisses += len(misses)
        if len(misses) != 0 and stop_on_miss:
            break

        # Put the device back on the queue with its updated age
        deviceQueue.put((currentDevice.localTime, currentDevice))

        # misses.clear()
        iteration += 1

    print("Simulated for {} microseconds".format(simulator_age))
    # print("Missed a total of {} deadlines when running for {} milliseconds".format(totalMisses, iteration*timeResolution/1000.0))
    wctt_sum = 0
    wctts = []

    for stream in streams:
        print("Stream{} WCTT: {} microseconds".format(stream.id, stream.WCTT))
        wctt_sum += stream.WCTT
        wctts.append(stream.WCTT)
    print("Device times in microseconds:")
    for device in network.nodes:
        print(device.localTime)
    print()
    print("Average WCTT: {} microseconds".format(round(wctt_sum / len(streams), 2)))
    print("Worst transmission time: {} microseconds".format(max(wctts)))
    logger.info("done.")

    return Results(network, streams, {})
