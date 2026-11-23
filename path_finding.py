"""Compatibility exports for the separated routing modules."""

from algo_solver import ConnectionManager, Zone as SolverZone
from manage_drones import manage_drones as separated_manage_drones
from manage_path import manager_path as separated_manager_path

# Backward-compatible alias for code that used the former misspelling.
dikstra_path = ConnectionManager.dijkstra_path

# Final bindings ensure legacy imports use the separated implementations.
Zone = SolverZone
connectionManager = ConnectionManager
manager_path = separated_manager_path
manage_drones = separated_manage_drones
