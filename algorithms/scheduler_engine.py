"""
algorithms/scheduler_engine.py
-------------------------------
End-to-End Intelligent Exam Scheduling Pipeline.

Key Pipeline Stages:
1. Conflict Graph Formulation
2. Chromatic Graph Coloring (Exact B&B, Backtracking CSP, or Greedy Heuristics)
3. Soft-Constraint Slot Permutation Optimization (Minimizing student consecutive exam fatigue)
4. Multi-Capacity Room Allocation (Best-Fit Decreasing Bin Packing)
5. Comprehensive Feasibility Validation & Metrics Aggregation
"""

import time
import math
import itertools
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

from models import (
    Course,
    Student,
    Room,
    TimeSlot,
    ScheduleResult,
    ScheduleMetrics,
)
from graph_builder import ConflictGraph
from algorithms.greedy_heuristics import GreedyColoring
from algorithms.exact_backtracking import BacktrackingCSPSolver
from algorithms.branch_and_bound import BranchAndBoundColoring


class IntelligentExamScheduler:
    """
    Main Scheduling Engine orchestrating graph coloring, soft-constraint optimization,
    and room capacity bin-packing.
    """

    def __init__(
        self,
        courses: List[Course],
        students: List[Student],
        rooms: List[Room],
        slots_per_day: int = 2,
    ):
        self.courses = courses
        self.students = students
        self.rooms = rooms
        self.slots_per_day = slots_per_day
        self.course_map = {c.id: c for c in courses}
        self.student_map = {s.id: s for s in students}
        self.room_map = {r.id: r for r in rooms}

        # Build conflict graph
        self.graph = ConflictGraph.build_from_enrollments(courses, students)

    def generate_schedule(
        self, algorithm: str = "branch_and_bound", max_slots: Optional[int] = None
    ) -> ScheduleResult:
        """
        Executes the full scheduling pipeline.

        Supported algorithms:
        - 'branch_and_bound' (Recommended exact/optimal)
        - 'dsatur' (Fast saturation heuristic)
        - 'welsh_powell' (Largest-degree greedy)
        - 'backtracking' (CSP with MRV & Forward Checking)
        """
        start_time = time.perf_counter()
        course_to_color: Dict[str, int] = {}
        algo_details: Dict[str, any] = {}

        # ---------------- Stage 1: Graph Coloring ----------------
        if algorithm == "welsh_powell":
            course_to_color, total_k, elapsed_algo = GreedyColoring.welsh_powell(
                self.graph
            )
            algo_details = {"algorithm": "Welsh-Powell", "elapsed_ms": elapsed_algo}

        elif algorithm == "dsatur":
            course_to_color, total_k, elapsed_algo = GreedyColoring.dsatur(self.graph)
            algo_details = {"algorithm": "DSatur", "elapsed_ms": elapsed_algo}

        elif algorithm == "backtracking":
            target_k = max_slots if max_slots else self.graph.get_max_degree()[1] + 1
            solver = BacktrackingCSPSolver(self.graph)
            sol, nodes, backtracks, elapsed_algo = solver.solve_k_colorable(
                target_k, use_forward_checking=True
            )
            if sol is None:
                # Fallback to DSatur if requested k is unfeasible
                sol, _, _ = GreedyColoring.dsatur(self.graph)
            course_to_color = sol
            algo_details = {
                "algorithm": "Backtracking CSP",
                "nodes_explored": nodes,
                "backtracks": backtracks,
                "elapsed_ms": elapsed_algo,
            }

        elif algorithm == "branch_and_bound":
            bnb_solver = BranchAndBoundColoring(self.graph)
            course_to_color, total_k, stats = bnb_solver.solve()
            algo_details = stats

        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        total_colors = max(course_to_color.values()) + 1 if course_to_color else 0

        # ---------------- Stage 2: Slot Ordering Optimization (Soft Constraints) ----------------
        # Optimize the permutation of color indices to minimize consecutive exam fatigue
        optimized_course_to_slot = self._optimize_slot_order(
            course_to_color, total_colors
        )

        # Build slot -> courses mapping
        slot_to_courses: Dict[int, List[str]] = defaultdict(list)
        for c_id, slot in optimized_course_to_slot.items():
            slot_to_courses[slot].append(c_id)

        # ---------------- Stage 3: Room Allocation (Bin Packing) ----------------
        room_allocations, room_violations = self._allocate_rooms(slot_to_courses)

        # ---------------- Stage 4: Metrics and Feasibility ----------------
        clashes = self._count_student_clashes(optimized_course_to_slot)
        consec_penalties, same_day_penalties = self._evaluate_student_fatigue(
            optimized_course_to_slot
        )
        variance = self._calculate_slot_variance(slot_to_courses)
        total_time_ms = (time.perf_counter() - start_time) * 1000.0

        is_feasible = (clashes == 0) and (room_violations == 0)

        metrics = ScheduleMetrics(
            total_slots_used=total_colors,
            chromatic_number_estimate=total_colors,
            student_conflict_count=clashes,
            room_capacity_violations=room_violations,
            consecutive_exam_penalties=consec_penalties,
            same_day_exam_penalties=same_day_penalties,
            slot_distribution_variance=round(variance, 2),
            execution_time_ms=round(total_time_ms, 2),
            algorithm_used=algorithm,
        )

        return ScheduleResult(
            course_to_slot=optimized_course_to_slot,
            slot_to_courses=dict(slot_to_courses),
            room_allocations=room_allocations,
            metrics=metrics,
            is_feasible=is_feasible,
            details=algo_details,
        )

    # ---------------- Soft-Constraint Permutation Optimization ----------------

    def _optimize_slot_order(
        self, course_to_color: Dict[str, int], total_colors: int
    ) -> Dict[str, int]:
        """
        Permutes the time slot indices to minimize consecutive exam penalties
        for students while strictly keeping conflict-free color groupings intact.

        For small k (<= 8), evaluates optimal permutation via brute-force.
        For larger k, uses greedy adjacent-swap local search.
        """
        if total_colors <= 1:
            return course_to_color

        # Invert: color -> list of courses
        color_groups: Dict[int, List[str]] = defaultdict(list)
        for c, col in course_to_color.items():
            color_groups[col].append(c)

        best_perm = list(range(total_colors))
        best_penalty = self._compute_perm_penalty(best_perm, color_groups)

        if total_colors <= 7:
            # Exact exhaustive permutation search (O(k!))
            for perm in itertools.permutations(range(total_colors)):
                pen = self._compute_perm_penalty(list(perm), color_groups)
                if pen < best_penalty:
                    best_penalty = pen
                    best_perm = list(perm)
        else:
            # 2-opt local search heuristic
            improved = True
            while improved:
                improved = False
                for i in range(total_colors - 1):
                    for j in range(i + 1, total_colors):
                        cand_perm = list(best_perm)
                        cand_perm[i], cand_perm[j] = cand_perm[j], cand_perm[i]
                        pen = self._compute_perm_penalty(cand_perm, color_groups)
                        if pen < best_penalty:
                            best_penalty = pen
                            best_perm = cand_perm
                            improved = True
                            break
                    if improved:
                        break

        # Map original colors to optimized slots
        color_map = {orig_col: new_slot for new_slot, orig_col in enumerate(best_perm)}
        return {c: color_map[col] for c, col in course_to_color.items()}

    def _compute_perm_penalty(
        self, perm: List[int], color_groups: Dict[int, List[str]]
    ) -> int:
        """Evaluates consecutive exam penalty for a given slot permutation."""
        course_slot: Dict[str, int] = {}
        for new_slot, orig_col in enumerate(perm):
            for c in color_groups[orig_col]:
                course_slot[c] = new_slot

        penalty = 0
        for student in self.students:
            slots = sorted([course_slot[c] for c in student.enrolled_courses if c in course_slot])
            for i in range(len(slots) - 1):
                if slots[i + 1] - slots[i] == 1:
                    penalty += 5  # High penalty for adjacent slots
                elif (slots[i + 1] // self.slots_per_day) == (slots[i] // self.slots_per_day):
                    penalty += 2  # Moderate penalty for same day
        return penalty

    # ---------------- Room Allocation (Bin Packing) ----------------

    def _allocate_rooms(
        self, slot_to_courses: Dict[int, List[str]]
    ) -> Tuple[Dict[str, List[str]], int]:
        """
        Allocates physical examination rooms to courses scheduled in each slot.
        Uses Best-Fit Decreasing (BFD) multi-room allocation.

        Returns: (course_to_rooms_map, total_capacity_violations)
        """
        course_room_alloc: Dict[str, List[str]] = {}
        violations = 0

        # Sort rooms by capacity descending
        sorted_rooms = sorted(self.rooms, key=lambda r: r.capacity, reverse=True)

        for slot, course_ids in slot_to_courses.items():
            # Available rooms in this time slot
            available_rooms = {r.id: r.capacity for r in sorted_rooms}

            # Sort courses in this slot by student count descending (Best-Fit Decreasing)
            courses_in_slot = sorted(
                [self.course_map[cid] for cid in course_ids if cid in self.course_map],
                key=lambda c: c.student_count,
                reverse=True,
            )

            for course in courses_in_slot:
                students_to_seat = course.student_count
                assigned_rooms: List[str] = []

                if students_to_seat == 0:
                    course_room_alloc[course.id] = []
                    continue

                # Try exact single-room fit first (Best-Fit)
                eligible_single = [
                    (r_id, cap)
                    for r_id, cap in available_rooms.items()
                    if cap >= students_to_seat
                ]

                if eligible_single:
                    # Pick room with minimal leftover capacity
                    best_room_id, _ = min(eligible_single, key=lambda x: x[1])
                    assigned_rooms.append(best_room_id)
                    del available_rooms[best_room_id]
                else:
                    # Multi-room split allocation (Greedy largest capacity first)
                    for r_id in list(available_rooms.keys()):
                        if students_to_seat <= 0:
                            break
                        cap = available_rooms[r_id]
                        assigned_rooms.append(r_id)
                        students_to_seat -= cap
                        del available_rooms[r_id]

                    if students_to_seat > 0:
                        # Seating capacity exceeded for this slot
                        violations += 1

                course_room_alloc[course.id] = assigned_rooms

        return course_room_alloc, violations

    # ---------------- Validation & Penalty Metrics ----------------

    def _count_student_clashes(self, course_to_slot: Dict[str, int]) -> int:
        """Counts how many students have 2 or more exams scheduled in the same time slot."""
        clashes = 0
        for student in self.students:
            slot_counts = defaultdict(int)
            for cid in student.enrolled_courses:
                if cid in course_to_slot:
                    slot = course_to_slot[cid]
                    slot_counts[slot] += 1
            for count in slot_counts.values():
                if count > 1:
                    clashes += (count - 1)
        return clashes

    def _evaluate_student_fatigue(
        self, course_to_slot: Dict[str, int]
    ) -> Tuple[int, int]:
        """Calculates consecutive exam and same-day exam counts across all students."""
        consecutive = 0
        same_day = 0

        for student in self.students:
            slots = sorted([course_to_slot[c] for c in student.enrolled_courses if c in course_to_slot])
            for i in range(len(slots) - 1):
                s1, s2 = slots[i], slots[i + 1]
                if s2 - s1 == 1:
                    consecutive += 1
                if (s1 // self.slots_per_day) == (s2 // self.slots_per_day) and s1 != s2:
                    same_day += 1

        return consecutive, same_day

    def _calculate_slot_variance(
        self, slot_to_courses: Dict[int, List[str]]
    ) -> float:
        """Calculates variance in student headcounts across all active time slots."""
        if not slot_to_courses:
            return 0.0
        counts = [
            sum(self.course_map[c].student_count for c in courses if c in self.course_map)
            for courses in slot_to_courses.values()
        ]
        mean = sum(counts) / len(counts)
        return sum((x - mean) ** 2 for x in counts) / len(counts)
