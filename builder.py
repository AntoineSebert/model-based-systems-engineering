import io
import xml.etree.ElementTree
from xml.dom import minidom
import networkx as nx
import matplotlib.pyplot as plt

from model import Network, Device

def build(file: io.TextIOWrapper) -> 'Network':
	tree = xml.etree.ElementTree.parse(file)
	root = tree.getroot()
	Network = nx.Graph()
	# Network2 = nx.petersen_graph()

	for child in root:
		if child.tag == 'device':
			node = Device(child.attrib['name'], child.attrib['type'])
			Network.add_node(node)
	for child in root:
		if child.tag == 'link':
			print("Adding edge from {0} to {1}".format(child.attrib['src'], child.attrib['dest']))
			Network.add_edge(Device(child.attrib['src'], "Nan"), Device(child.attrib['dest'], "Nan"), weight=float(child.attrib['speed']))

	plt.subplot(121)
	nx.draw(Network)
	plt.show()
	print(minidom.parseString(xml.etree.ElementTree.tostring(root)).toprettyxml(indent="  "))

