from itertools import combinations


from model import Solution, StreamSolution


def redundancyCheck(solution: Solution) -> dict['StreamSolution':bool]:
    redundant = [[streamSolution, True] for streamSolution in solution.streamSolutions]
    for index, streamSolution in enumerate(solution.streamSolutions):
        unique_links = set([link for route in streamSolution.routes for link in route.links])
        fault_tolerance = int(streamSolution.stream.rl) - 1
        if fault_tolerance > 0:
            link_combinations = combinations(unique_links, fault_tolerance)
            for comb in link_combinations:
                if all(bool(set(comb) & set(route.links)) for route in streamSolution.routes):
                    redundant[index][1] = False
    return redundant
