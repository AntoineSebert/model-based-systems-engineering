from itertools import combinations


from model import Solution, Stream


def redundancyCheck(solution: Solution) -> dict[Stream, bool]:
    '''

    Parameters
    ----------
    solution

    Returns
    -------
    A list of stream solutions and a bool for each denoting whether network topology supports the required redundancy level.
    True if so, False if no.
    '''

    redundant = [[True, stream] for stream in solution.stream]

    for index, stream in enumerate(solution.stream):
        unique_links = set([link for route in stream.routes for link in route.links])
        fault_tolerance = int(stream.rl) - 1

        if fault_tolerance > 0:
            link_combinations = combinations(unique_links, fault_tolerance)

            for comb in link_combinations:
                if all(bool(set(comb) & set(route.links)) for route in stream.routes):
                    redundant[index][0] = False

    return redundant