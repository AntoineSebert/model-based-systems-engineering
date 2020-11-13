from typing import Tuple
from typing import List
from xml.etree import ElementTree

class Device:
    def __init__(self, name: str, device_type: str):
        self.name = name
        self.device_type = device_type

    def __eq__(self, other):
        # Only equal by name (ID)
        if self.name == other.name:
            return True
        return False

    def __hash__(self):
        # print(hash(str(self)))
        return hash(str(self.name))

class streamInstance:
    def __init__(self):
        self.instance = 0

    @staticmethod
    def getInstance(self):
        self.instance = self.instance + 1
        return self.instance


class Stream:
    def __init__(self, id: str, src: Device, dest: Device, size: int, period: int, deadline: int, rl: int):
        self.id = id
        self.src = src
        self.dest = dest
        self.size = size
        self.period = period
        self.deadline = deadline
        self.rl = rl

    @classmethod
    def from_element(self, element: ElementTree):
        """
        Assuming element is structured as:
            <stream id="Stream1" src="ES2" dest="ES4" size="100" period="1000" deadline="10000" rl="2"/>
        """
        return self(**element.attrib)


# Is a sequence of steps on the form {(ES2 --> SW0), (SW0 --> ES3)}
class Route:
    def __init__(self, stream: Stream, route: List[Tuple[str, str]]):
        self.stream = stream
        self.route = route


# Solution output is:
# 1) A description of the network topology created
# 2) A list of routes for all periodic streams
class Solution:
    def __init__(self):
        pass
