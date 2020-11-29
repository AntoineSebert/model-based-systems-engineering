from model import Device, Link, Route, Stream, StreamSolution

from networkx import DiGraph  # type: ignore


from networkx.algorithms.simple_paths import all_simple_paths, shortest_simple_paths  # type: ignore


def search_all(network: DiGraph, src: Device, dest: Device):
	return all_simple_paths(network, src, dest)
