from datetime import datetime
from logging import getLogger
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, SubElement, indent

from model import Solution


def _add_streams(network_desc: Element, results: Solution) -> Element:
	"""Add the streams and their descendants into an XML element.

	Parameters
	----------
	network_desc : Element
		An XML element to hold the stream-related data.
	results : Solution
		Solution from which import the stream-related data.
	"""

	for stream in results.streams:
		stream_element = SubElement(network_desc, "stream", {
			"id": str(stream.id),
			"src": stream.src.name,
			"dest": stream.dest.name,
			"size": str(stream.size),
			"period": str(stream.period),
			"deadline": str(stream.deadline),
			"rl": str(stream.rl),
			"wctt": str(stream.WCTT),
		})

		for instance in stream.instances:
			instance_element = SubElement(stream_element, "instance", {"local_deadline": str(instance.local_deadline)})

			for framelet in instance.framelets:
				SubElement(instance_element, "framelet", {"id": str(framelet.id), "size": str(framelet.size)})

	return network_desc


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


def to_file(results: Solution, file: Path) -> Path:
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

	network_desc = Element("NetworkDescription", {"cost": str(results.monetaryCost()), "Redundancy_Ratio":str(results.redundancySatisfiedRatio()), "Deadlines_missed":"Yes" if len(results.misses) > 0 else "No"})
	worst_wctt = list(results.streams)[0].WCTT
	average_wctt = 0
	for stream in results.streams:
		if stream.WCTT > worst_wctt:
			worst_wctt = stream.WCTT
		average_wctt += stream.WCTT
	average_wctt = average_wctt / len(results.streams)

	SubElement(network_desc, "Worst_WCTT", {"Time": str(worst_wctt), "Unit": "Microseconds"})
	SubElement(network_desc, "Average_WCTT", {"Time": str(average_wctt), "Unit": "Microseconds"})

	for node in results.network:
		SubElement(network_desc, "device", {"name": node.name, "type": node.__class__.__name__})

	for u, v, speed in results.network.edges(data="speed"):
		SubElement(network_desc, "link", {"src": u.name, "dest": v.name, "speed": str(speed)})

	for stream in results.streams:
		SubElement(network_desc, "stream_times", {"id": stream.id, "WCTT" : str(stream.WCTT)})

	for time, streams in results.misses.items():
		miss = SubElement(network_desc, "miss", {"time": str(time)})

		for stream in streams:
			SubElement(miss, "stream", {"id": stream.id})

	network_desc = _add_streams(network_desc, results)

	root = ElementTree(network_desc)
	indent(root, space="\t")
	root.write(filepath, encoding='utf-8', xml_declaration=True)

	logger.info("done.")

	return filepath
