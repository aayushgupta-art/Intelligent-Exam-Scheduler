"""
algorithms/exact_backtracking.py
--------------------------------
Exact Constraint Satisfaction Problem (CSP) Backtracking Solver for Graph Coloring.

CSP Formalism:
- Variables (X): Vertices V = {v_1, v_2, ..., v_n}
- Domains (D): For each v in V, D(v) = {0, 1, ..., k-1} (Available time slots)
- Constraints (C): For all (u, v) in E, color(u) ≠ color(v)

Optimization Heuristics Integrated:
1. MRV (Minimum Remaining Values / Most Constrained Variable)
2. Degree Heuristic (Tie breaker on unassigned neighbors)
3. Forward Checking (Inference pruning during search)
4. LCV (Least Constraining Value ordering)
"""

import time
from typing import Dict, List, Set, Tuple, Optional
from graph_builder import ConflictGraph


class BacktrackingCSPSolver:
    """
    Solves the k-Coloring Decision Problem (and exact chromatic number search)
    using recursive backtracking with constraint propagation.
    """

    def __init__(self, graph: ConflictGraph, max_time_limit_sec: float = 10.0):
        self.graph = graph
        self.max_time_limit_sec = max_time_limit_sec
        self.nodes_explored = 0
        self.backtrack_count = 0
        self.timed_out = False

    def solve_k_colorable(
        self, k: int, use_forward_checking: bool = True
    ) -> Tuple[Optional[Dict[str, int]], int, int, float]:
        """
        Determines if G is k-colorable using backtracking CSP.

        Parameters:
        - k: Target number of colors (time slots: 0 .. k-1)
        - use_forward_checking: Whether to maintain and prune active domains.

        Returns: (assignment, nodes_explored, backtrack_count, elapsed_ms)
        """
        self.nodes_explored = 0
        self.backtrack_count = 0
        self.timed_out = False
        start_time = time.perf_counter()

        # Initialize domains for all vertices: {0, 1, ..., k-1}
        domains: Dict[str, Set[int]] = {
            v: set(range(k)) for v in self.graph.vertices
        }
        assignment: Dict[str, int] = {}

        success = self._backtrack(
            assignment, domains, k, use_forward_checking, start_time
        )
        elapsed = (time.perf_counter() - start_time) * 1000.0

        if success and not self.timed_out:
            return assignment, self.nodes_explored, self.backtrack_count, elapsed
        return None, self.nodes_explored, self.backtrack_count, elapsed

    def _select_unassigned_variable_mrv(
        self, assignment: Dict[str, int], domains: Dict[str, Set[int]]
    ) -> str:
        """
        Applies MRV (Minimum Remaining Values) heuristic with Degree Heuristic tie-breaking.
        1. Select variable with smallest domain size.
        2. In case of ties, select variable with highest number of unassigned neighbors.
        """
        unassigned = [v for v in self.graph.vertices if v not in assignment]

        def heuristic_key(v: str):
            domain_size = len(domains[v])
            unassigned_neighbors = sum(
                1 for nb in self.graph.adj_list[v] if nb not in assignment
            )
            return (domain_size, -unassigned_neighbors)

        return min(unassigned, key=heuristic_key)

    def _order_domain_values_lcv(
        self, var: str, domains: Dict[str, Set[int]], assignment: Dict[str, int]
    ) -> List[int]:
        """
        Least Constraining Value (LCV) Heuristic:
        Orders domain values by the count of neighbor domain choices they rule out (ascending).
        """
        def count_conflicts(val: int) -> int:
            conflicts = 0
            for nb in self.graph.adj_list[var]:
                if nb not in assignment and val in domains[nb]:
                    conflicts += 1
            return conflicts

        return sorted(list(domains[var]), key=count_conflicts)

    def _forward_check(
        self,
        var: str,
        color: int,
        domains: Dict[str, Set[int]],
        assignment: Dict[str, int],
    ) -> Optional[Dict[str, Set[int]]]:
        """
        Inference: Prunes `color` from all unassigned neighbors of `var`.
        Returns new domains if valid, or None if any neighbor's domain is wiped out.
        """
        new_domains = {v: set(d) for v, d in domains.items()}
        for nb in self.graph.adj_list[var]:
            if nb not in assignment:
                if color in new_domains[nb]:
                    new_domains[nb].remove(color)
                    if not new_domains[nb]:  # Domain wipe-out -> early failure
                        return None
        return new_domains

    def _backtrack(
        self,
        assignment: Dict[str, int],
        domains: Dict[str, Set[int]],
        k: int,
        use_forward_checking: bool,
        start_time: float,
    ) -> bool:
        """Recursive CSP Backtracking core engine."""
        self.nodes_explored += 1

        # Check timeout limit
        if (time.perf_counter() - start_time) > self.max_time_limit_sec:
            self.timed_out = True
            return False

        # Base case: All variables assigned
        if len(assignment) == self.graph.vertex_count:
            return True

        # Choose next variable using MRV + Degree Heuristic
        var = self._select_unassigned_variable_mrv(assignment, domains)
        ordered_values = self._order_domain_values_lcv(var, domains, assignment)

        for val in ordered_values:
            # Check consistency if not using forward checking
            if not use_forward_checking:
                conflict = any(
                    assignment.get(nb) == val for nb in self.graph.adj_list[var]
                )
                if conflict:
                    continue

            # Assign value
            assignment[var] = val

            if use_forward_checking:
                pruned_domains = self._forward_check(var, val, domains, assignment)
                if pruned_domains is not None:
                    if self._backtrack(
                        assignment, pruned_domains, k, True, start_time
                    ):
                        return True
            else:
                if self._backtrack(
                    assignment, domains, k, False, start_time
                ):
                    return True

            # Backtrack
            self.backtrack_count += 1
            del assignment[var]

        return False
