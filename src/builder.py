from io import TextIOWrapper
from logging import getLogger
from xml.etree.ElementTree import dump, indent, parse


from matplotlib import pyplot  # type: ignore

from model import Stream

from networkx import DiGraph, draw  # type: ignore


def build(file: TextIOWrapper) -> tuple[DiGraph, set[Stream]]:
	"""Prints the input file, builds the network and the streams, draws the graph and return the data.

	Parameters
	----------
	file : TextIOWrapper
		A *.app_network_description file from which import the network and streams.

	Returns
	-------
	tuple[DiGraph, set[Stream]]
		A tuple containing the network as a digraph and a set of streams.
	"""

	root = parse(file).getroot()

	indent(root, space="\t")
	dump(root)

	network = DiGraph()

	for device in root.iter("device"):
		network.add_node(device.get("name"), type=device.get("type"))

	for link in root.iter("link"):
		network.add_edge(link.get("src"), link.get("dest"), speed=link.get("speed"))

	pyplot.subplot(121)
	draw(network)
	pyplot.show()

	return (network, {Stream.from_element(stream) for stream in root.iter("stream")})
