# 3D night-city viewer

Pygame + PyOpenGL viewer for the Fly-in simulation (cyberpunk night city,
helicopter drones, neon landing pads).

    make install   # installs pygame-ce (same `import pygame`, works on Python 3.14)
    make run                      # simple fork demo
    python3 -m viewer3d MAP MOVES # your own map + simulation output
    your_simulator MAP | python3 -m viewer3d MAP -

Controls: SPACE play/pause, LEFT/RIGHT step, R restart, A auto-orbit,
T top view, left-drag to orbit, mouse wheel to zoom, ESC to quit.

MOVES is the simulator output: one line per turn, e.g. `D1-roof1 D2-hub-roof1`
(a `zone1-zone2` token means the drone is in flight toward a restricted zone).

From Python: `run_viewer(drone_map, Replay(drone_map, lines))`.

On Python 3.14 the official `pygame` 2.6.1 has no prebuilt wheel and may be
built without its font module: use `pygame-ce` (`pip uninstall pygame` first).

## Python API

    import viewer3d

    viewer3d.init(max_x, max_y)             # terrain 0..max_x, 0..max_y
    viewer3d.place_point(name, x, y)        # one point on the terrain
    viewer3d.place_connect([["a", "b"], ...])  # every connection
    viewer3d.show(moves=None)               # open the 3D window

- `init` must be called first (it also clears the previous scene). The terrain
  is drawn with a faint grid at every integer coordinate and grows by itself
  if a point is placed outside of it (e.g. negative `y`).
- `place_point` accepts optional keyword arguments: `kind` ("hub", "start",
  "end"), `zone_type`, `color`, `max_drones`.
- A connection can carry its capacity as a third element: `["a", "b", "2"]`.
- `show(moves, nb_drones)` replays the simulation output (one string per turn).
  Without moves it only displays the terrain, points and connections.
- Invalid input (unknown point, duplicate, dash in a name...) raises
  `ValueError`; calling `place_point` before `init` raises `RuntimeError`.

See `demo_api.py` for a complete example.
