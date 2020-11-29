from itertools import islice
from logging import getLogger
from pathlib import Path
from xml.etree.ElementTree import Element, dump, indent, parse

from model import EndSystem, InputPort, Link, Route, Stream, Switch

from networkx import DiGraph  # type: ignore

from networkx.algorithms.simple_paths import shortest_simple_paths  # type: ignore


def get_devices(root: Element, network: DiGraph) -> DiGraph:
	network.add_nodes_from(
		EndSystem(device.get("name"))
		if device.get("type") == "EndSystem" else Switch(device.get("name")) for device in root.iter("device")
	)

	return network


def create_links(root: Element, network: DiGraph) -> DiGraph:
	for link in root.iter("link"):
		src = next(node for node in network.nodes if node.name == link.get("src"))
		dest = next(node for node in network.nodes if node.name == link.get("dest"))

		network.add_edge(src, dest, speed=float(link.get('speed')))

		# what is this ?
		counter = 1
		while network.has_node(InputPort(dest.name + "$PORT" + str(counter))):
			counter += 1
		"""
		intermediateNode = InputPort(dest.name + "$PORT" + str(counter))
		network.add_edge(src, intermediateNode, speed=float(link.get('speed')))  # src to intermediate node
		network.add_edge(intermediateNode, dest, speed=0.0)  # intermediate node to dest
		"""

	return network


def findStreamSolution(network: DiGraph, stream: Stream) -> list[Route]:
	paths = list(islice(shortest_simple_paths(network, stream.src, stream.dest, weight='speed'), stream.rl))

	return [Route(i, [Link(path[ii], path[ii + 1]) for ii in range(len(path) - 1)]) for i, path in enumerate(paths)]


def create_streams(root: Element, network: DiGraph) -> set[Stream]:
	streams = {Stream.from_elementtree(stream, network) for stream in root.iter("stream")}

	for stream in streams:
		stream.routes = findStreamSolution(network, stream)

	return streams


def build(file: Path) -> tuple[DiGraph, set[Stream]]:
	"""Prints the input file, builds the network and the streams, draws the graph and return the data.

	Parameters
	----------
	file : Path
		An *.xml file from which import the network and streams.

	Returns
	-------
	tuple[DiGraph, set[Stream]]
		A tuple containing the network as a digraph and a set of streams.
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
