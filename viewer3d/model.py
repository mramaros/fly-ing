"""Map model and parser for the Fly-in input format."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ZONE_TYPES = ("normal", "blocked", "restricted", "priority")


class MapParseError(Exception):
    """Raised when the map file does not respect the expected syntax."""


@dataclass(frozen=True)
class Zone:
    """A zone (hub) of the network."""

    name: str
    x: int
    y: int
    kind: str = "hub"
    zone_type: str = "normal"
    color: str | None = None
    max_drones: int = 1


@dataclass(frozen=True)
class Link:
    """A bidirectional connection between two zones."""

    a: str
    b: str
    capacity: int = 1


@dataclass
class DroneMap:
    """A fully parsed and validated map."""

    nb_drones: int = 0
    zones: dict[str, Zone] = field(default_factory=dict)
    links: list[Link] = field(default_factory=list)
    start: str = ""
    end: str = ""
    bounds: tuple[int, int] | None = None

    def has_link(self, a: str, b: str) -> bool:
        """Return True if a connection exists between a and b."""
        return any({lk.a, lk.b} == {a, b} for lk in self.links)


_ZONE_RE = re.compile(
    r"^(start_hub|end_hub|hub):\s*(\S+)\s+(\S+)\s+(\S+)"
    r"\s*(?:\[(.*)\])?\s*$"
)
_LINK_RE = re.compile(
    r"^connection:\s*([^\s-]+)-([^\s-]+)\s*(?:\[(.*)\])?\s*$"
)


class MapParser:
    """Parse a Fly-in map file into a DroneMap."""

    def parse_file(self, path: str | Path) -> DroneMap:
        """Read and parse the file located at path."""
        with open(path, encoding="utf-8") as handle:
            return self.parse_text(handle.read())

    def parse_text(self, text: str) -> DroneMap:
        """Parse the map description contained in text."""
        dm = DroneMap()
        seen_header = False
        for number, raw in enumerate(text.splitlines(), start=1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            try:
                if not seen_header:
                    dm.nb_drones = self._parse_header(line)
                    seen_header = True
                elif line.startswith("connection:"):
                    self._parse_link(line, dm)
                else:
                    self._parse_zone(line, dm)
            except MapParseError as err:
                raise MapParseError(f"line {number}: {err}") from None
        if not seen_header:
            raise MapParseError("missing 'nb_drones' line")
        if not dm.start or not dm.end:
            raise MapParseError("need exactly one start_hub and one end_hub")
        return dm

    @staticmethod
    def _parse_header(line: str) -> int:
        match = re.match(r"^nb_drones:\s*(\S+)$", line)
        if not match or not match.group(1).isdigit():
            raise MapParseError("expected 'nb_drones: <positive_integer>'")
        value = int(match.group(1))
        if value < 1:
            raise MapParseError("nb_drones must be positive")
        return value

    @staticmethod
    def _parse_meta(
        text: str | None, allowed: tuple[str, ...]
    ) -> dict[str, str]:
        meta: dict[str, str] = {}
        for token in (text or "").split():
            key, sep, value = token.partition("=")
            if not sep or not key or not value:
                raise MapParseError(f"invalid metadata '{token}'")
            if key not in allowed:
                raise MapParseError(f"unknown metadata key '{key}'")
            if key in meta:
                raise MapParseError(f"duplicate metadata key '{key}'")
            meta[key] = value
        return meta

    @staticmethod
    def _positive(value: str, what: str) -> int:
        if not value.isdigit() or int(value) < 1:
            raise MapParseError(f"{what} must be a positive integer")
        return int(value)

    def _parse_zone(self, line: str, dm: DroneMap) -> None:
        match = _ZONE_RE.match(line)
        if not match:
            raise MapParseError(f"invalid zone definition '{line}'")
        prefix, name, sx, sy, raw_meta = match.groups()
        if "-" in name:
            raise MapParseError("zone names cannot contain dashes")
        if name in dm.zones:
            raise MapParseError(f"duplicate zone name '{name}'")
        try:
            x, y = int(sx), int(sy)
        except ValueError:
            raise MapParseError("coordinates must be integers") from None
        meta = self._parse_meta(
            raw_meta, ("zone", "color", "max_drones")
        )
        ztype = meta.get("zone", "normal")
        if ztype not in ZONE_TYPES:
            raise MapParseError(f"invalid zone type '{ztype}'")
        cap = 1
        if "max_drones" in meta:
            cap = self._positive(meta["max_drones"], "max_drones")
        kind = {"start_hub": "start", "end_hub": "end"}.get(prefix, "hub")
        if kind == "start" and dm.start:
            raise MapParseError("more than one start_hub")
        if kind == "end" and dm.end:
            raise MapParseError("more than one end_hub")
        dm.zones[name] = Zone(
            name, x, y, kind, ztype, meta.get("color"), cap
        )
        if kind == "start":
            dm.start = name
        elif kind == "end":
            dm.end = name

    def _parse_link(self, line: str, dm: DroneMap) -> None:
        match = _LINK_RE.match(line)
        if not match:
            raise MapParseError(f"invalid connection '{line}'")
        a, b, raw_meta = match.groups()
        for name in (a, b):
            if name not in dm.zones:
                raise MapParseError(f"unknown zone '{name}'")
        if dm.has_link(a, b):
            raise MapParseError(f"duplicate connection {a}-{b}")
        meta = self._parse_meta(raw_meta, ("max_link_capacity",))
        cap = 1
        if "max_link_capacity" in meta:
            cap = self._positive(
                meta["max_link_capacity"], "max_link_capacity"
            )
        dm.links.append(Link(a, b, cap))
