import io
import xml.etree.ElementTree

from model import Network, Device, Switch, EndSystem, Link, Stream, Solution, Route

def build(file: io.TextIOWrapper) -> 'Network':
	tree = ElementTree.parse(file)
	root = tree.getroot()

	print(root)

	#return Network(config, arch, graph)