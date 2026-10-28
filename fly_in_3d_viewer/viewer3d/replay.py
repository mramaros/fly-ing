"""Turn-by-turn replay of a simulation output."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .model import DroneMap


class ReplayError(Exception):
    """Raised when a simulation line is invalid for the given map."""


@dataclass(frozen=True)
class Location:
    """Where a drone is: in a zone, or in flight on a connection."""

    zone: str | None = None
    link: tuple[str, str] | None = None


_TOKEN_RE = re.compile(r"^D(\d+)-(.+)$")


class Replay:
    """Snapshots of every drone position after each simulation turn."""

    def __init__(self, drone_map: DroneMap, lines: list[str]) -> None:
        self.map = drone_map
        self.lines: list[str] = []
        start = Location(zone=drone_map.start)
        current = {i: start for i in range(1, drone_map.nb_drones + 1)}
        self.states: list[dict[int, Location]] = [dict(current)]
        for number, raw in enumerate(lines, start=1):
            line = raw.strip()
            if not line:
                continue
            for token in line.split():
                drone, loc = self._parse_token(token, number)
                current[drone] = loc
            self.lines.append(line)
            self.states.append(dict(current))

    @classmethod
    def from_text(cls, drone_map: DroneMap, text: str) -> Replay:
        """Build a replay from the raw simulation output."""
        return cls(drone_map, text.splitlines())

    @property
    def turns(self) -> int:
        """Number of simulation turns."""
        return len(self.states) - 1

    def delivered(self, index: int) -> int:
        """Number of drones in the end zone after the given turn."""
        end = self.map.end
        return sum(1 for v in self.states[index].values() if v.zone == end)

    def _parse_token(self, token: str, number: int) -> tuple[int, Location]:
        match = _TOKEN_RE.match(token)
        if not match:
            raise ReplayError(f"turn {number}: bad token '{token}'")
        drone = int(match.group(1))
        if not 1 <= drone <= self.map.nb_drones:
            raise ReplayError(f"turn {number}: unknown drone D{drone}")
        rest = match.group(2)
        if rest in self.map.zones:
            return drone, Location(zone=rest)
        a, _, b = rest.partition("-")
        if b and self.map.has_link(a, b):
            return drone, Location(link=(a, b))
        raise ReplayError(f"turn {number}: unknown target '{rest}'")
