from collections import defaultdict
from itertools import islice
from logging import getLogger
from math import lcm
from pathlib import Path
from xml.etree.ElementTree import Element, dump, indent, parse

from model import Device, EndSystem, Link, Scheduling, Stream, StreamInstance, Switch

from networkx import DiGraph  # type: ignore
from networkx.algorithms.connectivity.disjoint_paths import node_disjoint_paths  # type: ignore


def get_devices(root: Element, network: DiGraph) -> DiGraph:
	network.add_nodes_from(
		EndSystem(device.get("name"))
		if device.get("type") == "EndSystem"
		else Switch(device.get("name"))
		for device in root.iter("device")
	)

	return network


def create_links(root: Element, network: DiGraph) -> DiGraph:
	for link in root.iter("link"):
		network.add_edge(
			next(node for node in network.nodes if node.name == link.get("src")),
			next(node for node in network.nodes if node.name == link.get("dest")),
			speed=float(link.get('speed')),
		)

	return network


def create_streams(root: Element, network: DiGraph) -> set[Stream]:
	"""
	Raises
	------
	NetworkXNoPath
		From `node_disjoint_paths`, if no path from source to target could be found.
	"""
	streams: set[Stream] = set()

	for _stream in root.iter("stream"):
		stream = Stream(
			_stream.get("id"),
			next(node for node in network.nodes if node.name == _stream.get("src")),
			next(node for node in network.nodes if node.name == _stream.get("dest")),
			int(_stream.get("size")),
			int(_stream.get("period")),
			int(_stream.get("deadline")),
			int(_stream.get("rl")),
		)

		paths = list(islice(node_disjoint_paths(network, stream.src, stream.dest), stream.rl))
		stream.routes = [[Link(path[ii], path[ii + 1]) for ii in range(len(path) - 1)] for i, path in enumerate(paths)]

		streams.add(stream)

	return streams


def _compute_hyperperiod(streams: set[Stream]) -> int:
	"""Computes the hyperperiod.

	Parameters
	----------
	streams : set[Stream]
		Streams to compute a hyperperiod for.

	Returns
	-------
	int
		The hyperperiod for the streams.
	"""

	return lcm(*{stream.period for stream in streams})


def _get_emission_times(streams: set[Stream], hyperperiod: int) -> dict[int, set[Stream]]:
	"""Associates a time to a set of streams for emission.
	If for example we have the entry '(50, {stream0, stream3})', it means that the streams 'stream0' and 'stream3' are
	to be emitted at time 50, hyperperiod-wise.
	"""

	stream_emission_times: dict[Stream, set[int]] = {
		stream: {i * stream.period for i in range(int(hyperperiod / stream.period))} for stream in streams
	}
	emission_times: dict[int, set[Stream]] = defaultdict(set)

	for stream, times in stream_emission_times.items():
		for time in times:
			emission_times[time].add(stream)

	return emission_times


def _schedule_stream_emissions(streams: set[Stream], hyperperiod: int) -> Scheduling:
	"""Stream emission static scheduling. Check Model.Scheduling for more info."""

	emission_times = _get_emission_times(streams, hyperperiod)
	stream_emissions: dict[int, dict[EndSystem, set[StreamInstance]]] = {}

	for time, streams in emission_times.items():
		endsystem_emission: dict[EndSystem, set[StreamInstance]] = defaultdict(set)

		for stream in streams:
			endsystem_emission[stream.src].add(StreamInstance(stream, time + stream.deadline))

		stream_emissions[time] = endsystem_emission

	return stream_emissions


def _get_emitting_devices(network: DiGraph, streams: set[Stream]) -> set[Device]:
	"""Returns all the Devices that both:
	- have at least one outgoing edge
	- are on a route or stream source
	"""

	outgoing_devices: set[Device] = {u for u, v in network.out_edges()}
	emitting_devices: set[Device] = set()

	for device in outgoing_devices:
		for stream in streams:
			for route in stream.routes:
				if device in route:
					emitting_devices.add(device)
					break

	return emitting_devices


def _get_receiving_devices(network: DiGraph, streams: set[Stream]) -> set[Device]:
	"""Returns all the Devices that both:
	- have at least one ingoing edge
	- are on a route or stream dest
	"""

	ingoing_devices: set[Device] = {u for u, v in network.in_edges()}
	receiving_devices: set[Device] = set()

	for device in ingoing_devices:
		for stream in streams:
			for route in stream.routes:
				if device in route:
					receiving_devices.add(device)
					break

	return receiving_devices


def build(file: Path) -> tuple[DiGraph, set[Stream], Scheduling, set[Device], set[Device]]:
	"""Prints the input file, builds the network and the streams, draws the graph and return the data.

	Constraints
	----------
	We do not allow parallel edges between devices

	Parameters
	----------
	file : Path
		An *.xml file from which import the network and streams.

	Returns
	-------
	tuple[DiGraph, set[Stream]]
		A tuple containing the network as a DiGraph and a set of streams.
	"""

	logger = getLogger()
	logger.info(f"Importing the model from '{file}'...")

	root = parse(file).getroot()

	indent(root, space="\t")
	dump(root)

	network = create_links(root, get_devices(root, DiGraph()))
	streams = create_streams(root, network)
	hyperperiod = _compute_hyperperiod(streams)
	stream_emissions = _schedule_stream_emissions(streams, hyperperiod)

	logger.info("done.")

	return network, streams, stream_emissions, _get_emitting_devices(network, streams), _get_receiving_devices(network, streams)
