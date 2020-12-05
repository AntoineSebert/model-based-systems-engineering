from itertools import combinations
from networkx import DiGraph
from model import Switch

from model import Solution

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

def getCostFromSwitchDegree(degree: int) -> int:

    cost = 0
    
    #cost defined by automotive example.xlsx (multiplied by 2 to avoid using floats)

    if degree > 8:
        cost = 50 #penalty for exceeding number of allowed external ports
    elif degree == 2:
        cost = 2
    elif degree == 3:
        cost = 3
    elif degree == 4:
        cost = 5
    elif degree == 5:
        cost = 8
    elif degree == 6:
        cost = 9
    elif degree == 8:
        cost = 11
    else:
        print("SWITCH HAS DEGREE ", degree, " which is not allowed")
        cost = 50

    return cost

def monetaryCost(network: DiGraph) -> int:
    #nextStep = next(device for device in network. if link.src == self.name)
    cost = 0
    for device in network.nodes:
        if isinstance(device, Switch):
            degree = network.degree(device)
            currCost = getCostFromSwitchDegree(degree)
            print("Switch ", device.name, " has degree ", degree, " with cost ", currCost)
            cost += currCost
    return cost
