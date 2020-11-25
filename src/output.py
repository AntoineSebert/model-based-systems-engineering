from datetime import datetime
from logging import getLogger
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, SubElement, indent

from logic import Results


def _add_streams(network_desc: Element, results: Results) -> None:
	"""Add the streams and their descendants into an XML element.

	Parameters
	----------
	network_desc : Element
		An XML element to hold the stream-related data.
	results : Results
		Results from which import the stream-related data.
	"""

	for stream in results.streams:
		stream_element = SubElement(network_desc, "stream", {
			"id": str(stream.id),
			"src": stream.src,
			"dest": stream.dest,
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


def to_file(results: Results, file: Path) -> Path:
	"""Exports a result into a file.

	Parameters
	----------
	result : Result
		A result.
	file : Path
		An *.xml file from which import the network and streams.

	Returns
	-------
	filepath: Path
		An *.xml filepath where the results have been exported, depending on the input file name and the export time.
	"""

	logger = getLogger()

	filepath = _create_filepath(file)

	logger.info(f"Writing the best results into '{filepath.name}'...")

	network_desc = Element("NetworkDescription")

	for node in results.network:
		SubElement(network_desc, "device", {"name": node.name, "type": node.__class__.__name__})

	for u, v, speed in results.network.edges(data="speed"):
		SubElement(network_desc, "link", {"src": u.name, "dest": v.name, "speed": speed})

	_add_streams(network_desc, results)

	root = ElementTree(network_desc)
	indent(root, space="\t")
	root.write(filepath, encoding='utf-8', xml_declaration=True)

	# add metadata (cost function + worst case transmission time)

	logger.info("done.")

	return filepath
