import io
from networkx import DiGraph, draw
from xml.etree import ElementTree

#from model import Stream

def build(file: io.TextIOWrapper) -> tuple[DiGraph, set['Stream']]:
	root = ElementTree.parse(file).getroot()

	network = DiGraph()
	for device in root.iter("device"):
		network.add_node(device.get("name"), type=device.get("type"))

	for link in root.iter("link"):
		network.add_edge(link.get("src"), link.get("dest"), speed=link.get("speed"))

	draw(network)

	return (network, {Stream(stream) for stream in root.iter("stream")})