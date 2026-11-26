*This project has been created as part of the 42 curriculum by mramaros*

# Fly-In

## Description

Fly-In is a Python drone-routing simulator. It reads a map of hubs and
connections, finds routes from a start hub to an end hub, schedules drone
movements while respecting capacities, and displays the simulation in a 2D
Pygame window.

## Features

- Validates map files, hub definitions, and connections.
- Finds shortest and near-optimal routes while accounting for zone types.
- Schedules multiple drones around hub and connection capacity limits.
- Prints each turn's moves and animates the map in a 2D viewer.

## Instructions

Requirements: Python 3.10 or later and pip.

Create a virtual environment and install the dependencies:

```bash
make install
```

Run the default example map:

```bash
make run
```

Choose another map:

```bash
make run MAP=maps/medium/01_dead_end_trap.txt
```

Alternatively, run the program directly:

```bash
.venv/bin/python main.py maps/easy/01_linear_path.txt
```

The program prints movement instructions and opens a Pygame window. If Pygame
cannot be imported, it reports the missing dependency before reading the map.

## Map format

A map contains the number of drones, one start hub, one end hub, optional
intermediate hubs, and connections. Coordinates are integers. Lines may
include comments after `#`.

```text
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue] [zone=normal] [max_drones=1]
end_hub: goal 2 0 [color=red]

connection: start-waypoint1 [max_link_capacity=1]
connection: waypoint1-goal
```

Supported zone types are `normal`, `restricted`, `priority`, and `blocked`.
Connections are bidirectional; their capacity defaults to 1. Hub capacity
defaults to 1 for intermediate hubs. Start and end hubs can hold all drones.

## Algorithm and implementation

The map is represented as a graph: hubs are vertices and connections are
bidirectional edges. `algo_solver.py` searches paths with a min-priority queue.
Blocked hubs are excluded; entering a restricted hub costs 2, while entering
other traversable hubs costs 1. After finding the minimum cost, the solver
enumerates simple paths with a cost no more than 6 above that minimum, up to
100 candidate routes. It orders candidates by cost, preference for priority
hubs, route length, and name.

`manage_drones.py` assigns drones to candidate routes and simulates movement
turn by turn. It tracks hub occupancy and link usage so moves respect
`max_drones` and `max_link_capacity`. Restricted hubs use a two-step transit:
the drone first enters the connection and then arrives at the hub.

`parsing.py` and `constraint_parsing.py` read and validate map input.
`viewer2d.py` prepares map and replay data; `viewer2d_ui.py` handles the
Pygame rendering and controls.

## Visualization

The 2D viewer fits and centers the map in the window, draws connections and
named hubs, and animates drones at each simulation turn. Start and end hubs
have distinct colors; custom hub colors are supported. Drones sharing a
location are drawn side by side.

- **Left/Right arrows:** step through turns.
- **Space:** pause or resume.
- **R:** restart the replay.
- **Plus/Minus:** zoom in or out.
- **Up/Down:** increase or decrease playback speed.
- **Right mouse button + drag:** pan the map.
- **Escape:** close the viewer.

## Example

Input (`maps/easy/01_linear_path.txt`):

```text
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Expected movement output:

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

The Pygame window also opens and replays these four turns.

## Resources

- [Python documentation](https://docs.python.org/3/)
- [Python `heapq` documentation](https://docs.python.org/3/library/heapq.html)
- [Pygame documentation](https://www.pygame.org/docs/)
- [Dijkstra's algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)

AI assistance was used to split the 2D viewer into map/replay logic and a
Pygame interface, add a Pygame availability check at program startup, and
prepare this README. It was not used to replace the route solver or the
capacity-aware drone scheduler.
