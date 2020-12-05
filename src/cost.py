from itertools import combinations
from networkx import DiGraph
from model import Switch

from model import Solution

def redundancyCheck(solution: Solution) -> dict['StreamSolution':bool]:
    '''

    Parameters
    ----------
    solution

    Returns
    -------
    A list of stream solutions and a bool for each denoting whether network topology supports the required redundancy level.
    True if so, False if no.
    '''
    redundant = [[True, streamSolution] for streamSolution in solution.streamSolutions]
    for index, streamSolution in enumerate(solution.streamSolutions):
        unique_links = set([link for route in streamSolution.routes for link in route.links])
        fault_tolerance = int(streamSolution.stream.rl) - 1
        if fault_tolerance > 0:
            link_combinations = combinations(unique_links, fault_tolerance)
            for comb in link_combinations:
                if all(bool(set(comb) & set(route.links)) for route in streamSolution.routes):
                    redundant[index][0] = False
    return redundant

def redundancySatisfiedRatio(solution: Solution) -> float:

    redundant = redundancyCheck(solution)

    numOfSolutions = len(redundant)
    numOfSatisfied = 0.0

    numred = 0
    numregood = 0

    for sol in redundant:

        if sol[1].stream.rl == "2":
            numred += 1

        if sol[0]:
            numOfSatisfied += 1
            if sol[1].stream.rl == "2":
                numregood += 1
        else:
            print("Stream: ", sol[1].stream.id, " not satisfied ",sol[1].stream.src, " -> " , sol[1].stream.dest)

    print("Number of streams with rl2: ", numred, ", num of stream that satisfy rl2:" , numregood)

    ratio = (numOfSatisfied / numOfSolutions) * 100 #percentage of satisfied redundancy levels
    print("ratio: ", ratio)
    return ratio


def getCostFromSwitchDegree(degree: int) -> int:

    cost = 0
    
    #cost defined by automotive example.xlsx (multiplied by 2 to avoid using floats)

    if degree > 8:
        cost = 50 * (degree - 8) #penalty for exceeding number of allowed external ports
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
        cost = 500

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
