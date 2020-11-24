from datetime import datetime
from logging import getLogger
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, SubElement, indent

from logic import Solution


def _add_streams(network_desc: Element, solution: Solution) -> None:
	"""Add the streams and their descendants into an XML element.

	Parameters
	----------
	network_desc : Element
		An XML element to hold the stream-related data.
	solution : Solution
		A solution from which import the stream-related data.
	"""

	for stream in solution.streams:
		stream_element = SubElement(network_desc, "stream", {
			"id": str(stream.id),
			"src": stream.src.name,
			"dest": stream.dest.name,
			"size": str(stream.size),
			"period": str(stream.period),
			"deadline": str(stream.deadline),
			"rl": str(stream.rl),
		})

		for instance in stream.instances:
			instance_element = SubElement(stream_element, "instance", {"local_deadline": str(instance.local_deadline)})

			for framelet in instance.framelets:
				SubElement(instance_element, "framelet", {"id": str(framelet.id), "size": str(framelet.size)})


def _create_filepath(file: Path) -> Path:
	"""Creates a filepath from another file path.

	Parameters
	----------
	file : Path
		An *.xml file from which import the network and streams.

	Returns
	-------
	Path
		An *.xml filepath of the form 'name.datetime.xml'.
	"""

	suffix = datetime.now().strftime(".%Y-%m-%d-%H-%M-%S") + ".xml"
	new_file = file if len(file.suffixes) < 2 else file.parent / str(file.stem).split('.')[0]

	return new_file.with_suffix(suffix)


def to_file(solution: Solution, file: Path) -> Path:
	"""Exports a solution into a file.

	Parameters
	----------
	solution : Solution
		A solution.
	file : Path
		An *.xml file from which import the network and streams.

	Returns
	-------
	filepath: Path
		An *.xml filepath where the solution has been exported, depending on the input file name and the export time.
	"""

	logger = getLogger()

	filepath = _create_filepath(file)

	logger.info(f"Writing the best solution into '{filepath.name}'...")

	network_desc = Element("NetworkDescription")

	for node in solution.network:
		SubElement(network_desc, "device", {"name": node.name, "type": node.__class__.__name__})

	for u, v, speed in solution.network.edges(data="speed"):
		SubElement(network_desc, "link", {"src": u.name, "dest": v.name, "speed": speed})

	_add_streams(network_desc, solution)

	root = ElementTree(network_desc)
	indent(root, space="\t")
	root.write(filepath, encoding='utf-8', xml_declaration=True)

	# add metadata (cost function + worst case transmission time)

	logger.info("done.")

	return filepath
