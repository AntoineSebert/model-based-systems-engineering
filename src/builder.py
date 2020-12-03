from itertools import islice
from logging import getLogger
from pathlib import Path
from xml.etree.ElementTree import Element, dump, indent, parse

from model import EndSystem, InputPort, Link, Route, Stream, Switch

from networkx import DiGraph  # type: ignore

from networkx.algorithms.connectivity.disjoint_paths import node_disjoint_paths  # type: ignore


def get_devices(root: Element, network: DiGraph) -> DiGraph:
	network.add_nodes_from(
		EndSystem(device.get("name"))
		if device.get("type") == "EndSystem" else Switch(device.get("name")) for device in root.iter("device")
	)

	return network


def create_links(root: Element, network: DiGraph) -> DiGraph:
	for link in root.iter("link"):
		network.add_edge(
			next(node for node in network.nodes if node.name == link.get("src")),
			next(node for node in network.nodes if node.name == link.get("dest")),
			speed=float(link.get('speed'))
		)

	return network

def create_streams(root: Element, network: DiGraph) -> set[Stream]:
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
		paths = list(islice(node_disjoint_paths(network, stream.src, stream.dest, weight='speed'), stream.rl))
		stream.routes = [Route(i, [Link(path[ii], path[ii + 1]) for ii in range(len(path) - 1)]) for i, path in enumerate(paths)]

		streams.add(stream)

	return streams


def build(file: Path) -> tuple[DiGraph, set[Stream]]:
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

	logger.info("done.")

	return network, streams
