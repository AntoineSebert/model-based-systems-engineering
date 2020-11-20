
from logging import getLogger
from pathlib import Path
from xml.etree.ElementTree import indent


from model import Solution, Switch, EndSystem


def to_file(solution: Solution, folder: Path) -> Path:
	logger = getLogger()

	filepath: Path = args.folder / (args.folder.stem + ".xml")
	logger.info(f"Writing the best solution into '{filepath}'...")

	filepath.touch(exist_ok=False)

	root = ElementTree(Element("simulation"))

	network = SubElement(root, "Network")
	network_desc = SubElement(root, "networkDescription")
	config = SubElement(root, "Configuration")
	tasks = SubElement(root, "graphml")

	for node in solution.network:
		SubElement(network_desc, "device", {"name": node.name, "type": node.__class__.__name__})

	for u, v, speed in solution.network.edges(data="speed"):
		SubElement(network_desc, "link", {"src": u.name, "src": u.name, "speed": speed})

	for stream in solution.streams:
		for dest, rl in stream.dest.items():
			SubElement(network_desc, "stream", {
				"id": stream.name,
				"src": stream.src,
				"dest": stream.dest,
				"size": stream.size,
				"period": stream.period,
				"deadline": stream.deadline,
				"rl": stream.rl,
			})

	indent(root, space="\t")

	with filepath.open(mode='w', encoding='utf-8') as file:
		root.write(file, encoding='utf-8')

	# add metadata (cost function + worst case transmission time)

	logger.log("done.")

	return filepath