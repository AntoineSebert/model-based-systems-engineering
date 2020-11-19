from typing import Tuple
from typing import List
from xml.etree import ElementTree
from dataclasses import dataclass


@dataclass
class Device:
    name: str

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, Device):
            return self.name == other.name
        return False


@dataclass(eq=False)
class Switch(Device):
    speed: float = 1.0


@dataclass(eq=False)
class EndSystem(Device):
    pass


# Solution output is:
# 1) A description of the network topology created
# 2) A list of routes for all periodic streams
class Solution:
    def __init__(self):
        pass
