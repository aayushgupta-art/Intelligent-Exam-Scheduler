"""
algorithms/greedy_heuristics.py
-------------------------------
Implementation of Greedy Graph Coloring Heuristics for Fast Upper-Bound Approximation.

Implemented Algorithms:
1. Welsh-Powell Algorithm (Largest Degree First - LDF)
   - Sorts vertices by degree descending.
   - Color each uncolored vertex with smallest valid color.
   - Worst-case Time Complexity: O(|V|^2 + |E|)

2. DSatur Algorithm (Degree of Saturation - Brélaz, 1979)
   - Dynamically prioritizes vertices with highest saturation degree
     (number of distinct colors among adjacent vertices).
   - Ties broken by uncolored subgraph degree.
   - Worst-case Time Complexity: O(|V|^2) with binary heaps or arrays.

3. First-Fit (Basic Sequential Greedy)
   - Colors vertices in arbitrary or input order.
   - Worst-case Time Complexity: O(|V| + |E|)
"""

import time
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from graph_builder import ConflictGraph


class GreedyColoring:
    """Provides heuristic graph coloring solvers to establish upper bounds."""

    @staticmethod
    def welsh_powell(graph: ConflictGraph) -> Tuple[Dict[str, int], int, float]:
        """
        Welsh-Powell Algorithm (1967).

        Steps:
        1. Order vertices in descending order of degree: deg(v1) >= deg(v2) >= ... >= deg(vn).
        2. Assign color 0 to first uncolored vertex in sorted list.
        3. Iterate through remaining vertices: assign current color to any vertex
           not adjacent to any vertex already assigned this color.
        4. Repeat with next color until all vertices are colored.

        Returns: (coloring_dict, chromatic_upper_bound, elapsed_time_ms)
        Time Complexity: O(|V| log |V| + |V|^2)
        Space Complexity: O(|V|)
        """
        start_time = time.perf_counter()
        ordered_vertices = graph.compute_welsh_powell_ordering()
        colors: Dict[str, int] = {}
        current_color = 0

        uncolored = list(ordered_vertices)

        while uncolored:
            # Color the first uncolored vertex
            colored_in_this_pass: List[str] = []

            for v in uncolored:
                # Check if v is adjacent to any vertex colored in this pass
                has_conflict = False
                for cv in colored_in_this_pass:
                    if cv in graph.adj_list[v]:
                        has_conflict = True
                        break

                if not has_conflict:
                    colors[v] = current_color
                    colored_in_this_pass.append(v)

            # Remove colored vertices
            uncolored = [v for v in uncolored if v not in colors]
            current_color += 1

        elapsed = (time.perf_counter() - start_time) * 1000.0
        total_colors = current_color
        return colors, total_colors, elapsed

    @staticmethod
    def dsatur(graph: ConflictGraph) -> Tuple[Dict[str, int], int, float]:
        """
        DSatur (Degree of Saturation) Algorithm (Daniel Brélaz, 1979).

        Heuristic:
        1. Select uncolored vertex with maximal saturation degree
           (number of different colors used by its neighbors).
        2. If tied, pick vertex with maximal degree in the uncolored subgraph.
        3. Assign it the smallest available valid color index.
        4. Update saturation degrees of neighbors and repeat.

        Returns: (coloring_dict, total_colors, elapsed_time_ms)
        Time Complexity: O(|V|^2)
        Space Complexity: O(|V| + |E|)
        """
        start_time = time.perf_counter()
        colors: Dict[str, int] = {}
        n = graph.vertex_count

        if n == 0:
            return {}, 0, 0.0

        # Track colors assigned to neighbor vertices for each vertex
        neighbor_colors: Dict[str, Set[int]] = {v: set() for v in graph.vertices}
        # Degree in uncolored graph
        uncolored_degrees: Dict[str, int] = {v: graph.degree(v) for v in graph.vertices}

        # Step 1: First vertex is one with max degree
        first_v, _ = graph.get_max_degree()
        colors[first_v] = 0
        for neighbor in graph.adj_list[first_v]:
            neighbor_colors[neighbor].add(0)
            uncolored_degrees[neighbor] -= 1

        # Step 2: Color remaining n - 1 vertices
        for _ in range(n - 1):
            # Find uncolored vertex with max saturation degree
            best_v = None
            max_sat = -1
            max_deg = -1

            for v in graph.vertices:
                if v not in colors:
                    sat = len(neighbor_colors[v])
                    deg = uncolored_degrees[v]

                    if sat > max_sat or (sat == max_sat and deg > max_deg):
                        max_sat = sat
                        max_deg = deg
                        best_v = v

            if best_v is None:
                break

            # Find lowest available color for best_v
            used_by_neighbors = neighbor_colors[best_v]
            assigned_color = 0
            while assigned_color in used_by_neighbors:
                assigned_color += 1

            colors[best_v] = assigned_color

            # Update neighbors
            for neighbor in graph.adj_list[best_v]:
                neighbor_colors[neighbor].add(assigned_color)
                uncolored_degrees[neighbor] -= 1

        elapsed = (time.perf_counter() - start_time) * 1000.0
        total_colors = max(colors.values()) + 1 if colors else 0
        return colors, total_colors, elapsed

    @staticmethod
    def first_fit(graph: ConflictGraph) -> Tuple[Dict[str, int], int, float]:
        """
        Standard Sequential First-Fit Greedy Algorithm.

        Time Complexity: O(|V| + |E|)
        Space Complexity: O(|V|)
        """
        start_time = time.perf_counter()
        colors: Dict[str, int] = {}

        for v in graph.vertices:
            neighbor_colors = {colors[nb] for nb in graph.adj_list[v] if nb in colors}
            c = 0
            while c in neighbor_colors:
                c += 1
            colors[v] = c

        elapsed = (time.perf_counter() - start_time) * 1000.0
        total_colors = max(colors.values()) + 1 if colors else 0
        return colors, total_colors, elapsed
