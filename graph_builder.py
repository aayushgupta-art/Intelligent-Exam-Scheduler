"""
graph_builder.py
----------------
Constructs and analyzes the Course Conflict Graph G = (V, E).

Mathematical Formulation:
- V = { c_1, c_2, ..., c_n } (Courses)
- E = { (u, v) | Enrollment(u) ∩ Enrollment(v) ≠ ∅ } (Clash Edges)
- Weight w(u, v) = |Enrollment(u) ∩ Enrollment(v)| (Number of mutually enrolled students)
- Chromatic Lower Bound: ω(G) ≤ χ(G) (Max Clique Size ≤ Chromatic Number)
"""

from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import math
from models import Course, Student


class ConflictGraph:
    """
    Mathematical Graph representation of course exam conflicts.
    Provides adjacency lists, edge weights, degree analysis, and clique lower bounds.
    """

    def __init__(self):
        self.vertices: Set[str] = set()
        self.adj_list: Dict[str, Set[str]] = defaultdict(set)
        self.edge_weights: Dict[Tuple[str, str], int] = {}
        self.student_clashes: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
        self.courses_map: Dict[str, Course] = {}

    def add_course(self, course: Course) -> None:
        """Adds a course vertex to the graph."""
        self.vertices.add(course.id)
        self.courses_map[course.id] = course
        if course.id not in self.adj_list:
            self.adj_list[course.id] = set()

    def add_conflict(self, u: str, v: str, student_id: str) -> None:
        """Adds or updates an edge between two conflicting courses due to a shared student."""
        if u == v:
            return
        self.vertices.add(u)
        self.vertices.add(v)
        self.adj_list[u].add(v)
        self.adj_list[v].add(u)

        edge_key = tuple(sorted((u, v)))
        self.student_clashes[edge_key].add(student_id)
        self.edge_weights[edge_key] = len(self.student_clashes[edge_key])

    @classmethod
    def build_from_enrollments(
        cls, courses: List[Course], students: List[Student]
    ) -> "ConflictGraph":
        """
        Factory method to construct the conflict graph directly from course and student lists.
        Time Complexity: O(|S| * k^2) where |S| is number of students and k is max courses per student.
        """
        graph = cls()

        # Register all courses
        for course in courses:
            graph.add_course(course)

        # Map student enrollments
        for student in students:
            enrolled = list(student.enrolled_courses)
            for i in range(len(enrolled)):
                # Link student to course object
                if enrolled[i] in graph.courses_map:
                    graph.courses_map[enrolled[i]].enrolled_students.add(student.id)

                for j in range(i + 1, len(enrolled)):
                    u, v = enrolled[i], enrolled[j]
                    graph.add_conflict(u, v, student.id)

        return graph

    # ---------------- Graph Properties & Asymptotic Metrics ----------------

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)

    @property
    def edge_count(self) -> int:
        return sum(len(neighbors) for neighbors in self.adj_list.values()) // 2

    def degree(self, v: str) -> int:
        """Returns the degree d(v) of vertex v."""
        return len(self.adj_list.get(v, set()))

    def get_max_degree(self) -> Tuple[str, int]:
        """Returns vertex with maximum degree Δ(G)."""
        if not self.vertices:
            return ("", 0)
        max_v = max(self.vertices, key=lambda v: self.degree(v))
        return (max_v, self.degree(max_v))

    def get_min_degree(self) -> Tuple[str, int]:
        """Returns vertex with minimum degree δ(G)."""
        if not self.vertices:
            return ("", 0)
        min_v = min(self.vertices, key=lambda v: self.degree(v))
        return (min_v, self.degree(min_v))

    def density(self) -> float:
        """
        Calculates graph density D = 2|E| / (|V|(|V|-1)).
        Density ranges between 0.0 (empty graph) and 1.0 (complete graph K_n).
        """
        v_n = self.vertex_count
        if v_n <= 1:
            return 0.0
        return (2.0 * self.edge_count) / (v_n * (v_n - 1))

    def get_edge_weight(self, u: str, v: str) -> int:
        """Returns number of shared students between course u and v."""
        edge_key = tuple(sorted((u, v)))
        return self.edge_weights.get(edge_key, 0)

    # ---------------- Theoretical Bounding Functions ----------------

    def compute_welsh_powell_ordering(self) -> List[str]:
        """
        Orders vertices in non-ascending order of their degrees:
        deg(v_1) >= deg(v_2) >= ... >= deg(v_n).
        Time Complexity: O(|V| log |V|)
        """
        return sorted(list(self.vertices), key=lambda v: self.degree(v), reverse=True)

    def find_max_clique_heuristic(self) -> Set[str]:
        """
        Computes a maximal clique in G using a greedy heuristic to establish
        a lower bound for the Chromatic Number: ω(G) <= χ(G).

        Algorithm:
        1. Pick vertex v with max degree.
        2. Iteratively add candidate vertex sharing edges with all current clique members.
        Time Complexity: O(|V|^2)
        """
        if not self.vertices:
            return set()

        sorted_vertices = self.compute_welsh_powell_ordering()
        max_clique: Set[str] = set()

        for start_v in sorted_vertices[: min(5, len(sorted_vertices))]:
            current_clique = {start_v}
            candidates = set(self.adj_list[start_v])

            while candidates:
                # Pick candidate connected to the most current candidate members
                best_cand = max(
                    candidates,
                    key=lambda c: len(self.adj_list[c].intersection(candidates)),
                )
                # Verify best_cand is adjacent to all vertices in current_clique
                if current_clique.issubset(self.adj_list[best_cand]):
                    current_clique.add(best_cand)
                    candidates.remove(best_cand)
                else:
                    candidates.remove(best_cand)

            if len(current_clique) > len(max_clique):
                max_clique = current_clique

        return max_clique

    def get_chromatic_lower_bound(self) -> int:
        """Lower bound on slots: max clique size ω(G)."""
        clique = self.find_max_clique_heuristic()
        return max(1, len(clique))

    def get_summary_dict(self) -> Dict[str, any]:
        """Returns diagnostic properties of the conflict graph."""
        max_v, max_deg = self.get_max_degree()
        min_v, min_deg = self.get_min_degree()
        clique = self.find_max_clique_heuristic()
        return {
            "total_courses": self.vertex_count,
            "total_clashes": self.edge_count,
            "density": round(self.density(), 4),
            "max_degree": f"{max_deg} (Course: {max_v})",
            "min_degree": f"{min_deg} (Course: {min_v})",
            "clique_lower_bound_omega": len(clique),
            "sample_max_clique": list(clique),
        }
