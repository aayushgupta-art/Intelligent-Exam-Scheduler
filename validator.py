"""
validator.py
------------
Formal Invariant Verification & Integrity Checker for Exam Schedules.

Performs rigorous checks across all academic constraints:
1. Hard Conflict Invariant: Zero student clashes (No student has overlapping exams).
2. Graph Adjacency Invariant: Adjacent vertices have strictly distinct colors.
3. Completeness Invariant: All enrolled courses are scheduled exactly once.
4. Room Double-Booking Invariant: No room is allocated to multiple courses in the same slot.
5. Capacity Invariant: Allocated rooms provide sufficient seats for enrolled students.
"""

from typing import List, Dict, Tuple, Set
from collections import defaultdict
from models import Course, Student, Room, ScheduleResult
from graph_builder import ConflictGraph


class ScheduleValidator:
    """Rigorous audit suite to verify all hard and soft constraints of a schedule."""

    @staticmethod
    def validate(
        schedule: ScheduleResult,
        courses: List[Course],
        students: List[Student],
        rooms: List[Room],
        graph: ConflictGraph,
    ) -> Tuple[bool, List[str], Dict[str, any]]:
        """
        Runs comprehensive validation tests.

        Returns:
        - is_valid (bool): True if ALL hard constraints pass.
        - error_log (List[str]): List of violation descriptions (empty if valid).
        - summary (Dict): Formatted report of audit.
        """
        error_log: List[str] = []
        course_map = {c.id: c for c in courses}
        room_map = {r.id: r for r in rooms}
        slot_map = schedule.course_to_slot

        # ---------------- Check 1: Completeness ----------------
        scheduled_courses = set(slot_map.keys())
        all_courses = {c.id for c in courses}
        missing = all_courses - scheduled_courses
        if missing:
            error_log.append(f"[FAIL] Completeness: {len(missing)} courses unscheduled: {missing}")

        # ---------------- Check 2: Graph Adjacency Invariant ----------------
        edge_violations = 0
        for u in graph.vertices:
            for v in graph.adj_list[u]:
                if u in slot_map and v in slot_map:
                    if slot_map[u] == slot_map[v]:
                        edge_violations += 1
                        error_log.append(
                            f"[FAIL] Graph Adjacency: Conflict edge between '{u}' and '{v}' sharing slot {slot_map[u]}"
                        )
        edge_violations //= 2  # Undirected edges counted twice

        # ---------------- Check 3: Student-Level Overlap Check ----------------
        student_clashes = 0
        clashing_students: List[str] = []
        for s in students:
            enrolled = [cid for cid in s.enrolled_courses if cid in slot_map]
            seen_slots: Dict[int, str] = {}
            for cid in enrolled:
                slot = slot_map[cid]
                if slot in seen_slots:
                    student_clashes += 1
                    clashing_students.append(s.id)
                    error_log.append(
                        f"[FAIL] Student Clash: Student '{s.name}' ({s.id}) has conflicting exams in Slot {slot}: "
                        f"'{seen_slots[slot]}' and '{cid}'"
                    )
                else:
                    seen_slots[slot] = cid

        # ---------------- Check 4: Room Double-Booking ----------------
        room_clashes = 0
        for slot, c_ids in schedule.slot_to_courses.items():
            allocated_rooms_in_slot: Set[str] = set()
            for cid in c_ids:
                assigned = schedule.room_allocations.get(cid, [])
                for r_id in assigned:
                    if r_id in allocated_rooms_in_slot:
                        room_clashes += 1
                        error_log.append(
                            f"[FAIL] Room Double-Booking: Room '{r_id}' double-booked in Slot {slot} by course '{cid}'"
                        )
                    allocated_rooms_in_slot.add(r_id)

        # ---------------- Check 5: Room Capacity Compliance ----------------
        capacity_shortages = 0
        for cid, r_ids in schedule.room_allocations.items():
            if cid in course_map:
                needed = course_map[cid].student_count
                total_cap = sum(room_map[rid].capacity for rid in r_ids if rid in room_map)
                if total_cap < needed:
                    capacity_shortages += 1
                    error_log.append(
                        f"[FAIL] Room Capacity: Course '{cid}' needs {needed} seats but allocated {total_cap} in rooms {r_ids}"
                    )

        is_valid = (len(error_log) == 0)

        summary = {
            "is_valid": is_valid,
            "total_courses_audited": len(courses),
            "total_students_audited": len(students),
            "total_slots_used": schedule.metrics.total_slots_used,
            "graph_edge_violations": edge_violations,
            "student_clashes": student_clashes,
            "room_double_bookings": room_clashes,
            "room_capacity_shortages": capacity_shortages,
            "status": "PASSED (Conflict-Free)" if is_valid else "FAILED",
        }

        return is_valid, error_log, summary
