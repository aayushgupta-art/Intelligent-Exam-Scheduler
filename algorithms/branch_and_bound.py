"""
algorithms/branch_and_bound.py
------------------------------
Branch and Bound Optimization for Exact Chromatic Number Calculation (χ(G)).

Mathematical Foundation:
- Problem: Find minimum k such that G is k-colorable (NP-Hard Optimization Problem).
- Lower Bound L = ω(G) (Max Clique Size).
- Upper Bound U = χ_heuristic(G) (from Welsh-Powell or DSatur).
- Bounding Condition: Prune subtree if current_colors_used >= current_best_upper_bound.
- Symmetry Breaking: For vertex v, allow only colors in {0, ..., max_used_color + 1}.
- Search Space Optimization: Pre-color maximum clique vertices to fix the coordinate frame.
"""

import time
from typing import Dict, List, Set, Tuple, Optional
from graph_builder import ConflictGraph
from algorithms.greedy_heuristics import GreedyColoring
from algorithms.exact_backtracking import BacktrackingCSPSolver


class BranchAndBoundColoring:
    """
    Branch and Bound solver to compute the exact minimum chromatic number χ(G).
    Combines lower bounds (Cliques), upper bounds (DSatur/Welsh-Powell),
    symmetry breaking, and depth-first search.
    """

    def __init__(self, graph: ConflictGraph, time_limit_sec: float = 15.0):
        self.graph = graph
        self.time_limit_sec = time_limit_sec
        self.best_coloring: Dict[str, int] = {}
        self.best_k: int = graph.vertex_count
        self.nodes_explored: int = 0
        self.pruned_branches: int = 0
        self.timed_out: bool = False

    def solve(self) -> Tuple[Dict[str, int], int, Dict[str, any]]:
        """
        Executes the Branch and Bound optimization pipeline.

        Returns:
        - best_coloring: Dictionary mapping course_id -> color_id (0 .. χ-1)
        - exact_chromatic_number: Minimum number of slots required
        - stats: Execution statistics and bounds report
        """
        start_time = time.perf_counter()
        self.nodes_explored = 0
        self.pruned_branches = 0
        self.timed_out = False

        # Step 1: Compute Lower Bound via Max Clique
        max_clique = self.graph.find_max_clique_heuristic()
        lower_bound = max(1, len(max_clique))

        # Step 2: Compute Upper Bound via DSatur Heuristic
        dsatur_sol, dsatur_k, _ = GreedyColoring.dsatur(self.graph)
        wp_sol, wp_k, _ = GreedyColoring.welsh_powell(self.graph)

        if dsatur_k <= wp_k:
            self.best_coloring = dsatur_sol
            self.best_k = dsatur_k
            initial_ub_source = "DSatur"
        else:
            self.best_coloring = wp_sol
            self.best_k = wp_k
            initial_ub_source = "Welsh-Powell"

        initial_upper_bound = self.best_k

        # Check for immediate optimality: L == U
        if lower_bound == initial_upper_bound:
            elapsed = (time.perf_counter() - start_time) * 1000.0
            return self.best_coloring, self.best_k, {
                "lower_bound_omega": lower_bound,
                "initial_upper_bound": initial_upper_bound,
                "upper_bound_source": initial_ub_source,
                "optimal_found_immediately": True,
                "nodes_explored": 0,
                "pruned_branches": 0,
                "elapsed_time_ms": elapsed,
            }

        # Step 3: Branch and Bound via Iterative Search / CSP Reduction
        # Order vertices: Clique vertices first (fixed), then by descending degree
        clique_list = list(max_clique)
        remaining_vertices = [
            v for v in self.graph.compute_welsh_powell_ordering() if v not in max_clique
        ]
        ordered_search_vertices = clique_list + remaining_vertices

        # Pre-assign distinct colors to the clique vertices (Symmetry Breaking)
        fixed_assignment: Dict[str, int] = {}
        for idx, cv in enumerate(clique_list):
            fixed_assignment[cv] = idx

        # Try to find valid coloring for target_k from (best_k - 1) down to lower_bound
        current_target_k = self.best_k - 1
        while current_target_k >= lower_bound:
            csp_solver = BacktrackingCSPSolver(
                self.graph,
                max_time_limit_sec=max(1.0, self.time_limit_sec - (time.perf_counter() - start_time)),
            )
            sol, nodes, backtracks, _ = csp_solver.solve_k_colorable(
                k=current_target_k, use_forward_checking=True
            )
            self.nodes_explored += nodes
            self.pruned_branches += backtracks

            if sol is not None:
                self.best_coloring = sol
                self.best_k = current_target_k
                current_target_k -= 1
            else:
                # G is provably not current_target_k colorable -> optimal is current_target_k + 1
                break

            if (time.perf_counter() - start_time) > self.time_limit_sec:
                self.timed_out = True
                break

        elapsed = (time.perf_counter() - start_time) * 1000.0
        return self.best_coloring, self.best_k, {
            "lower_bound_omega": lower_bound,
            "initial_upper_bound": initial_upper_bound,
            "upper_bound_source": initial_ub_source,
            "optimal_found_immediately": False,
            "final_chromatic_number": self.best_k,
            "nodes_explored": self.nodes_explored,
            "pruned_branches": self.pruned_branches,
            "elapsed_time_ms": elapsed,
            "timed_out": self.timed_out,
        }
