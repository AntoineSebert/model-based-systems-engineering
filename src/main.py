from argparse import ArgumentParser
from logging import INFO, WARNING, getLogger

from builder import build

from output import to_file


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
		'-s', '--scheduler',
		default="strict-priority",
		choices=["strict-priority"],
		help="Scheduling algorithm, either one of: 'strict-priority'",
		metavar="SCHEDULER",
		dest="scheduler",
	)
	parser.add_argument(
		"-f", "--file",
		type=open,
		required=True,
		help="Import network description from FILE.",
		metavar='FILE',
		dest="file",
	)
	parser.add_argument(
		"--verbose",
		action="store_true",
		help="Toggle program verbosity.",
		default=False,
	)
	parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

	return parser


def main() -> int:
	args = _create_cli_parser().parse_args()

	getLogger().setLevel(INFO if args.verbose else WARNING)

	network, streams = build(args.file)

	solution = simulate(network, streams)

	to_file(solution, args.folder)

	exit()


if __name__ == "__main__":
	main()
