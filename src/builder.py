from io import TextIOWrapper
from logging import getLogger
from xml.etree.ElementTree import dump, indent, parse
from matplotlib import pyplot  # type: ignore

from model import Stream, EndSystem, Switch, Device

from networkx import DiGraph, draw, spring_layout  # type: ignore
from numpy import sqrt


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

	# Find devices
	for device in root.iter("device"):
		device_type = device.get("type")
		device_name = device.get("name")
		if device_type == "EndSystem":
			network.add_node(EndSystem(device_name))
		elif device_type == "Switch":
			network.add_node(Switch(device_name))

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

	return (network, {Stream.from_element(stream) for stream in root.iter("stream")})