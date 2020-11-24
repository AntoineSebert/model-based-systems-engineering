from logging import getLogger
from pathlib import Path
from xml.etree.ElementTree import dump, indent, parse

from logic import Stream

from matplotlib import pyplot  # type: ignore

from model import EndSystem, Switch

from networkx import DiGraph, draw, spring_layout  # type: ignore

from numpy import sqrt  # type: ignore


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

	network = DiGraph()

	# Find devices
	for device in root.iter("device"):
		if (device_type := device.get("type")) == "EndSystem":
			network.add_node(EndSystem(device.get("name")))
		elif device_type == "Switch":
			network.add_node(Switch(device.get("name")))

	# Connect devices by links

	for link in root.iter("link"):
		print("Adding a link from {0} to {1}".format(link.get("src"), link.get("dest")))
		# This is not working
		src = None
		dest = None

		# Determine src type
		if str(link.get("src")).startswith("SW"):
			src = Switch(link.get("src"))
		else:
			src = EndSystem(link.get("src"))
		# Determine destination type
		if str(link.get("dest")).startswith("SW"):
			dest = Switch(link.get("dest"))
		else:
			dest = EndSystem(link.get("dest"))
		network.add_edge(src, dest, speed=link.get("speed"))

	print("Number of network devices: {}".format(len(network.nodes)))
	print(network.nodes)
	print("Number of network links: {}".format(len(network.edges)))
	print(network.edges)

	pos = spring_layout(network, k=2 / sqrt(len(network.nodes())), iterations=50)
	pyplot.subplots(figsize=(30, 30))
	pyplot.subplot(121)
	draw(network, pos=pos)
	pyplot.show()

	streams = {Stream(
		stream.get("id"),
		[node for node, data in network.nodes(data=True) if node.name == stream.get("src")][0],
		[node for node, data in network.nodes(data=True) if node.name == stream.get("dest")][0],
		stream.get("size"),
		stream.get("period"),
		stream.get("deadline"),
		stream.get("rl"),
		set(),
	) for stream in root.iter("stream")}

	logger.info("done.")

	return network, streams
