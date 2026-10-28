"""Command line entry point: python -m viewer3d MAP [MOVES|-]."""

from __future__ import annotations

import argparse
import sys

from .app import Viewer
from .model import MapParseError, MapParser
from .replay import Replay, ReplayError


def main() -> int:
    """Parse the arguments and start the viewer."""
    parser = argparse.ArgumentParser(prog="viewer3d")
    parser.add_argument("map_file", help="map file (e.g. maps/easy/...)")
    parser.add_argument("moves", nargs="?",
                        help="simulation output file, or '-' for stdin")
    parser.add_argument("--size", default="1280x720", help="WIDTHxHEIGHT")
    parser.add_argument("--snapshot", metavar="PNG",
                        help="save one frame and quit")
    parser.add_argument("--turn", type=float, default=0.0,
                        help="turn position used with --snapshot")
    parser.add_argument("--focus", metavar="ZONE",
                        help="aim the camera at a zone (with --zoom)")
    parser.add_argument("--zoom", type=float, default=1.0,
                        help="zoom factor applied with --focus")
    args = parser.parse_args()
    try:
        width, height = (int(v) for v in args.size.lower().split("x"))
        drone_map = MapParser().parse_file(args.map_file)
        text = ""
        if args.moves == "-":
            text = sys.stdin.read()
        elif args.moves:
            with open(args.moves, encoding="utf-8") as handle:
                text = handle.read()
        replay = Replay.from_text(drone_map, text)
    except (MapParseError, ReplayError, OSError, ValueError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    viewer = Viewer(drone_map, replay, (width, height))
    if args.focus:
        if args.focus not in drone_map.zones:
            print(f"Error: unknown zone '{args.focus}'", file=sys.stderr)
            return 1
        viewer.focus(args.focus, args.zoom)
    if args.snapshot:
        viewer.snapshot(args.snapshot, args.turn)
    else:
        viewer.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
