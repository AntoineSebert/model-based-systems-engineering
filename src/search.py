from networkx.algorithms.simple_paths import all_simple_paths as ap
from networkx.algorithms.shortest_paths import all_shortest_paths as asp

from model import StreamSolution, Route, Link, Device, Switch, EndSystem


def search_all(network, src, dest):
    return ap(network, src, dest)


def k_shortest(network, src, dest):
    return asp(network, src, dest, weight='speed')


def findRoutes(pathGenerator, k):
    routes = []

    for counter, path in enumerate(pathGenerator):
        # Separate route into individual steps and store
        route = Route(counter + 1, [])
        for index in range(len(path) - 1):
            route.links.append(Link(path[index].name, path[index + 1].name))
        routes.append(route)
        # stream_solution.routes.append(route)

        # Check if all streams covered
        if counter == k - 1:
            break
    return routes


def findStreamSolution(network, stream) -> StreamSolution:
    # Determine src type
    src = None
    dest = None
    if str(stream.src).startswith("SW"):
        src = Switch(stream.src)
    else:
        src = EndSystem(stream.src)
    # Determine destination type
    if str(stream.dest).startswith("SW"):
        dest = Switch(stream.dest)
    else:
        dest = EndSystem(stream.dest)

    print("\nFinding path from {0} to {1}".format(src.name, dest.name))
    streamSolution = StreamSolution(stream, [])
    try:
        pathGenerator = k_shortest(network, src, dest)
        streamSolution.routes.extend(findRoutes(pathGenerator, int(stream.rl)))

        print("Found at least 1 path\n")
    except:
        print("!!!There exists no paths from {0} to {1} !!!\n".format(src.name, dest.name))
    return streamSolution