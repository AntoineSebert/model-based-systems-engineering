# Simulation of ADAS interconnection network

## Motivation

The overall goal of this project is to develop and present a tool, that may aid in the assessment of the value of a given networks and streams, such that it may be applied to the development of TSN systems.

## Getting Started

### Programming Language

This project has been created with Python 3.9, that you can get at https://www.python.org/.
We recommend the installation of pip (https://pip.pypa.io/en/stable/) for the following steps.

### Third-party Libraries

We make use of matplotlib (https://matplotlib.org/) for the network display and networkx (https://networkx.org/) for the graph data structure.
Assuming pip has been installed, you can simply do :

```
pip install matplotlib networkx
```

## Running the Simulator

In this section, we will be working from the project's root directory.

### Command-Line Interface

The CLI can simply be exposed with:

```
python src/main.py --help
```

Then we can simply write :

```
python src/main.py -f data/PreemptionTest.xml -t 5000
```

Note: The network description files are typically stored in `/data/`, but it is not a requirement.

## Authors

Casper Egholm Jørgensen s163950

Danial Virk s193167

Lawrence Egyir s160146

Óli Kárason Mikkelsen s174269

Saadman Haq s160081

Antoine Louis Thibaut Sébert s193508
