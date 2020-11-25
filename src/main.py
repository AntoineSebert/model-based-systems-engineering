from argparse import ArgumentParser
from logging import INFO, WARNING, getLogger
from pathlib import Path

from builder import build

from output import to_file

from simulator import simulate


def _create_cli_parser() -> ArgumentParser:
	"""Creates a CLI argument parser and returns it.

	Returns
	-------
	parser : ArgumentParser
		An `ArgumentParser` holding part of the program's CLI.
	"""

	parser = ArgumentParser(
		prog="Time-Sensitive Network Simulator",
		description="Determine efficiency of network technologies used given certain system configurations in regards \
			of safety and performance.",
		allow_abbrev=True,
	)

	parser.add_argument(
		"-f", "--file",
		type=Path,
		required=True,
		help="Import network description from FILE.",
		metavar='FILE',
		dest="file",
	)
	parser.add_argument(
		"-t", "--time-limit",
		type=int,
		default=-1,
		help="A time limitation for the simulation, in simulation time (or, the iteration limit).",
		metavar='TIME',
		dest="time",
	)
	parser.add_argument(
		"-s", "--stop-on-miss",
		action='store_true',
		help="Toggles whether the simulation stops when a deadline miss happens or not.",
		dest="stop",
	)
	parser.add_argument(
		"--verbose",
		action="store_true",
		help="Toggle program verbosity.",
		default=False,
	)
	parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
	parser.add_argument("-dg", "--display-graph", action="store_true", help="Display network as graph", dest="display_graph")

	return parser


def main() -> int:
	args = _create_cli_parser().parse_args()

	getLogger().setLevel(INFO if args.verbose else WARNING)

	network, streams = build(args.file, args.display_graph)

	solution = simulate(network, streams, args.time, args.stop)

	to_file(solution, args.file)

	exit()


if __name__ == "__main__":
	main()
