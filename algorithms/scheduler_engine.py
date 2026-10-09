"""
algorithms/scheduler_engine.py
-------------------------------
End-to-End Intelligent Exam Scheduling Pipeline for Enterprise Universities.

Key Pipeline Stages:
1. Conflict Graph Formulation & Clique Lower Bounding
2. Chromatic Graph Coloring (Exact B&B, Backtracking CSP with MRV/FC, or Greedy Heuristics)
3. Soft-Constraint Slot Permutation Optimization (Minimizing student consecutive exam fatigue)
4. Strict Multi-Capacity Room Allocation (Best-Fit Decreasing Multi-Hall Bin Packing)
5. Calendar Date & Exact Clock Time Window Synthesis
6. Anti-Paper-Leak Synchronization & Invariant Verification
"""

import time
import math
import itertools
from datetime import datetime, date, timedelta
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict

from models import (
    Course,
    Student,
    Room,
    RoomSeatAllocation,
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
    strict room capacity multi-hall bin-packing, real-world calendar windows,
    and anti-paper-leak section synchronization.
    """

    DEFAULT_SESSION_TIMINGS_2 = [
        ("Morning Session", "09:30 AM", "12:30 PM", "09:30 AM - 12:30 PM"),
        ("Afternoon Session", "02:00 PM", "05:00 PM", "02:00 PM - 05:00 PM"),
    ]

    DEFAULT_SESSION_TIMINGS_3 = [
        ("Morning Session", "09:00 AM", "12:00 PM", "09:00 AM - 12:00 PM"),
        ("Afternoon Session", "01:30 PM", "04:30 PM", "01:30 PM - 04:30 PM"),
        ("Evening Session", "05:30 PM", "08:30 PM", "05:30 PM - 08:30 PM"),
    ]

    def __init__(
        self,
        courses: List[Course],
        students: List[Student],
        rooms: List[Room],
        slots_per_day: int = 2,
        exam_start_date: str = "2026-11-16",
    ):
        self.courses = courses
        self.students = students
        self.rooms = rooms
        self.slots_per_day = max(1, slots_per_day)
        self.exam_start_date = exam_start_date

        self.course_map: Dict[str, Course] = {c.id: c for c in courses}
        self.student_map: Dict[str, Student] = {s.id: s for s in students}
        self.room_map: Dict[str, Room] = {r.id: r for r in rooms}

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
        algo_details: Dict[str, Any] = {}

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

        # ---------------- Stage 3: Strict Multi-Capacity Room Allocation (Bin Packing) ----------------
        room_allocations, room_allocation_details, room_violations, split_count, total_seats = (
            self._allocate_rooms(slot_to_courses)
        )

        # ---------------- Stage 4: Calendar Date & Real Time Windows ----------------
        time_slots = self._synthesize_calendar_time_slots(total_colors)
        calendar_days_spanned = math.ceil(total_colors / self.slots_per_day) if total_colors > 0 else 0

        # ---------------- Stage 5: Anti-Paper-Leak Synchronization Audit ----------------
        synced_papers, leak_vulns = self._audit_paper_leak_synchronization(optimized_course_to_slot)

        # ---------------- Stage 6: Metrics and Feasibility Aggregation ----------------
        clashes = self._count_student_clashes(optimized_course_to_slot)
        consec_penalties, same_day_penalties = self._evaluate_student_fatigue(
            optimized_course_to_slot
        )
        variance = self._calculate_slot_variance(slot_to_courses)
        total_time_ms = (time.perf_counter() - start_time) * 1000.0

        is_feasible = (clashes == 0) and (room_violations == 0) and (leak_vulns == 0)

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
            calendar_days_spanned=calendar_days_spanned,
            synchronized_papers_count=synced_papers,
            paper_leak_vulnerabilities=leak_vulns,
            multi_room_splits_count=split_count,
            total_seats_allocated=total_seats,
        )

        return ScheduleResult(
            course_to_slot=optimized_course_to_slot,
            slot_to_courses=dict(slot_to_courses),
            room_allocations=room_allocations,
            room_allocation_details=room_allocation_details,
            time_slots=time_slots,
            metrics=metrics,
            is_feasible=is_feasible,
            details=algo_details,
        )

    # ---------------- Calendar & Real Time Slot Synthesis ----------------

    def _synthesize_calendar_time_slots(self, total_slots: int) -> Dict[int, TimeSlot]:
        """
        Synthesizes real calendar dates and precise clock time windows for every slot.
        """
        time_slots: Dict[int, TimeSlot] = {}
        try:
            base_date = datetime.strptime(self.exam_start_date, "%Y-%m-%d").date()
        except Exception:
            base_date = date(2026, 11, 16)

        timings = (
            self.DEFAULT_SESSION_TIMINGS_3
            if self.slots_per_day >= 3
            else self.DEFAULT_SESSION_TIMINGS_2
        )

        for slot_id in range(total_slots):
            day_idx = slot_id // self.slots_per_day
            sess_idx = slot_id % self.slots_per_day
            sess_info = timings[min(sess_idx, len(timings) - 1)]

            # Compute calendar date (advancing weekdays, skipping Sundays)
            current_date = base_date
            added_days = 0
            while added_days < day_idx:
                current_date += timedelta(days=1)
                # Skip Sundays for standard academic examinations
                if current_date.weekday() != 6:
                    added_days += 1

            cal_date_str = current_date.strftime("%Y-%m-%d")
            formatted_date_str = current_date.strftime("%A, %d %b %Y")
            session_name = f"Session {sess_idx + 1} ({sess_info[0].split()[0]})"
            start_t = sess_info[1]
            end_t = sess_info[2]
            time_win = sess_info[3]
            label = f"Slot #{slot_id + 1}: {current_date.strftime('%d-%b-%Y')} ({time_win})"

            time_slots[slot_id] = TimeSlot(
                id=slot_id,
                day_index=day_idx,
                calendar_date=cal_date_str,
                formatted_date=formatted_date_str,
                session_name=session_name,
                start_time=start_t,
                end_time=end_t,
                time_window=time_win,
                label=label,
            )

        return time_slots

    # ---------------- Strict Multi-Capacity Room Allocation (Bin Packing) ----------------

    def _allocate_rooms(
        self, slot_to_courses: Dict[int, List[str]]
    ) -> Tuple[Dict[str, List[str]], Dict[str, List[RoomSeatAllocation]], int, int, int]:
        """
        Allocates physical examination rooms to courses scheduled in each slot.
        Enforces STRICT room capacity:
        - No room is assigned more students than its physical capacity (allocated_seats <= capacity).
        - If a course's student headcount exceeds any single room, it is partitioned across
          multiple eligible rooms using Best-Fit Decreasing Multi-Hall Bin Packing.

        Returns:
        - course_room_alloc: Dict[course_id, List[room_id]]
        - course_room_details: Dict[course_id, List[RoomSeatAllocation]]
        - total_capacity_violations: int
        - multi_room_splits_count: int
        - total_seats_allocated: int
        """
        course_room_alloc: Dict[str, List[str]] = {}
        course_room_details: Dict[str, List[RoomSeatAllocation]] = {}
        violations = 0
        split_count = 0
        total_seats_allocated = 0

        # Sort rooms by capacity descending
        sorted_rooms = sorted(self.rooms, key=lambda r: r.capacity, reverse=True)

        for slot, course_ids in slot_to_courses.items():
            # Available rooms in this time slot (copy of full room inventory)
            available_rooms: List[Room] = list(sorted_rooms)

            # Sort courses in this slot by student count descending (Best-Fit Decreasing)
            courses_in_slot = sorted(
                [self.course_map[cid] for cid in course_ids if cid in self.course_map],
                key=lambda c: c.student_count,
                reverse=True,
            )

            for course in courses_in_slot:
                needed_students = course.student_count
                allocations: List[RoomSeatAllocation] = []

                if needed_students == 0:
                    course_room_alloc[course.id] = []
                    course_room_details[course.id] = []
                    continue

                # Case 1: Try Best Single-Room Fit
                eligible_single_rooms = [
                    r for r in available_rooms if r.capacity >= needed_students
                ]

                if eligible_single_rooms:
                    # Pick eligible room with minimal leftover capacity (Best-Fit)
                    best_room = min(
                        eligible_single_rooms, key=lambda r: (r.capacity - needed_students)
                    )
                    allocations.append(
                        RoomSeatAllocation(
                            room_id=best_room.id,
                            room_name=best_room.name,
                            capacity=best_room.capacity,
                            allocated_seats=needed_students,
                        )
                    )
                    available_rooms.remove(best_room)
                    total_seats_allocated += needed_students

                else:
                    # Case 2: Multi-Room Partitioning (Course exceeds single hall capacity)
                    remaining_to_seat = needed_students
                    rooms_used_for_split = 0

                    for room in list(available_rooms):
                        if remaining_to_seat <= 0:
                            break
                        seats_in_this_room = min(remaining_to_seat, room.capacity)
                        allocations.append(
                            RoomSeatAllocation(
                                room_id=room.id,
                                room_name=room.name,
                                capacity=room.capacity,
                                allocated_seats=seats_in_this_room,
                            )
                        )
                        remaining_to_seat -= seats_in_this_room
                        total_seats_allocated += seats_in_this_room
                        available_rooms.remove(room)
                        rooms_used_for_split += 1

                    if rooms_used_for_split > 1:
                        split_count += 1

                    if remaining_to_seat > 0:
                        # Insufficient total venue capacity in this time slot
                        violations += 1

                course_room_alloc[course.id] = [a.room_id for a in allocations]
                course_room_details[course.id] = allocations

        return (
            course_room_alloc,
            course_room_details,
            violations,
            split_count,
            total_seats_allocated,
        )

    # ---------------- Anti-Paper-Leak Synchronization Audit ----------------

    def _audit_paper_leak_synchronization(
        self, course_to_slot: Dict[str, int]
    ) -> Tuple[int, int]:
        """
        Audits that all cohorts, sections, and courses sharing the same common paper code
        are scheduled at the exact same time slot, preventing question paper leakage across sessions.
        """
        paper_to_slots: Dict[str, Set[int]] = defaultdict(set)
        for c in self.courses:
            if c.id in course_to_slot:
                p_code = getattr(c, "paper_code", c.code)
                paper_to_slots[p_code].add(course_to_slot[c.id])

        leak_vulnerabilities = 0
        synchronized_papers = 0

        for p_code, slots in paper_to_slots.items():
            if len(slots) == 1:
                synchronized_papers += 1
            else:
                leak_vulnerabilities += 1

        return synchronized_papers, leak_vulnerabilities

    # ---------------- Soft-Constraint Permutation Optimization ----------------

    def _optimize_slot_order(
        self, course_to_color: Dict[str, int], total_colors: int
    ) -> Dict[str, int]:
        """
        Permutes the time slot indices to minimize consecutive exam penalties
        for students while strictly keeping conflict-free color groupings intact.
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
            slots = sorted(
                [course_slot[c] for c in student.enrolled_courses if c in course_slot]
            )
            for i in range(len(slots) - 1):
                if slots[i + 1] - slots[i] == 1:
                    penalty += 5  # High penalty for adjacent slots
                elif (slots[i + 1] // self.slots_per_day) == (
                    slots[i] // self.slots_per_day
                ):
                    penalty += 2  # Moderate penalty for same day
        return penalty

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
                    clashes += count - 1
        return clashes

    def _evaluate_student_fatigue(
        self, course_to_slot: Dict[str, int]
    ) -> Tuple[int, int]:
        """Calculates consecutive exam and same-day exam counts across all students."""
        consecutive = 0
        same_day = 0

        for student in self.students:
            slots = sorted(
                [course_to_slot[c] for c in student.enrolled_courses if c in course_to_slot]
            )
            for i in range(len(slots) - 1):
                diff = slots[i + 1] - slots[i]
                if diff == 1:
                    consecutive += 1
                if (slots[i + 1] // self.slots_per_day) == (slots[i] // self.slots_per_day):
                    same_day += 1

        return consecutive, same_day

    def _calculate_slot_variance(
        self, slot_to_courses: Dict[int, List[str]]
    ) -> float:
        """Computes statistical variance in student headcount across time slots."""
        if not slot_to_courses:
            return 0.0

        slot_headcounts = []
        for courses in slot_to_courses.values():
            total_students_in_slot = sum(
                self.course_map[cid].student_count
                for cid in courses
                if cid in self.course_map
            )
            slot_headcounts.append(total_students_in_slot)

        mean_hc = sum(slot_headcounts) / len(slot_headcounts)
        variance = sum((x - mean_hc) ** 2 for x in slot_headcounts) / len(
            slot_headcounts
        )
        return variance
