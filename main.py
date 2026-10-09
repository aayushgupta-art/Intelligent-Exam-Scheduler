"""
main.py
-------
Main Execution Driver for the Intelligent University Exam Scheduling System.

Demonstrates:
1. Conflict Graph Generation & Asymptotic Graph Properties (Density, Max Degree, Clique Bound)
2. Execution of Greedy Heuristics (Welsh-Powell, DSatur), CSP Backtracking, and Branch & Bound
3. Enterprise Timetable Presentation with Calendar Dates, Exact Clock Time Windows,
   Academic Year/Semester Metadata, and Strict Room Capacity Distribution
4. Comprehensive 6-Invariant Integrity Audit including Anti-Paper-Leak Verification
"""

import sys
import time
from typing import List, Any

from sample_data import get_academic_dataset
from graph_builder import ConflictGraph
from algorithms.scheduler_engine import IntelligentExamScheduler
from validator import ScheduleValidator


def print_banner():
    print("=" * 100)
    print("   INTELLIGENT UNIVERSITY EXAM SCHEDULING SYSTEM (ENTERPRISE DAA CAPSTONE)")
    print("   Graph Colouring, Exact Backtracking, Strict Capacity BFD & Anti-Paper-Leak Engine")
    print("=" * 100)


def format_table(headers: List[str], rows: List[List[Any]]) -> str:
    """Simple terminal table formatter with proper column padding."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    row_fmt = " | ".join([f"{{:<{w}}}" for w in col_widths])
    sep = "-+-".join(["-" * w for w in col_widths])

    lines = [
        row_fmt.format(*headers),
        sep,
    ]
    for row in rows:
        lines.append(row_fmt.format(*[str(c) for c in row]))
    return "\n".join(lines)


def main():
    print_banner()

    # Step 1: Load Dataset
    courses, students, rooms = get_academic_dataset()
    print(f"\n[1] ACADEMIC DATASET INITIALIZED:")
    print(f"    - Total Courses (|V|)        : {len(courses)} (Core & Elective Engineering)")
    print(f"    - Total Student Records (|S|): {len(students)} (Spanning CSE, AIML, CSDS, IT, ECE, Honors)")
    print(f"    - Available Exam Halls & Labs: {len(rooms)} (Capacities: 50 to 250 seats)")
    print(f"    - Exam Block Start Date      : 2026-11-16 (Monday, 16 Nov 2026)")

    # Step 2: Build & Analyze Conflict Graph
    graph = ConflictGraph.build_from_enrollments(courses, students)
    summary = graph.get_summary_dict()

    print(f"\n[2] CONFLICT GRAPH ANALYSIS (G = (V, E)):")
    print(f"    - Total Vertices (|V|)   : {summary['total_courses']}")
    print(f"    - Total Conflict Edges (|E|): {summary['total_clashes']}")
    print(f"    - Graph Density (D)       : {summary['density']} (Highly Interconnected)")
    print(f"    - Max Degree Δ(G)         : {summary['max_degree']}")
    print(f"    - Min Degree δ(G)         : {summary['min_degree']}")
    print(f"    - Lower Bound ω(G) [Clique]: {summary['clique_lower_bound_omega']} slots (Theoretical Minimum)")
    print(f"    - Sample Maximal Clique   : {summary['sample_max_clique']}")

    # Step 3: Comparative Evaluation Across Algorithms
    print(f"\n[3] MULTI-ALGORITHM BENCHMARK ON CONFLICT GRAPH:")
    algorithms = ["welsh_powell", "dsatur", "backtracking", "branch_and_bound"]
    comp_headers = [
        "Algorithm",
        "Total Slots (k)",
        "Time (ms)",
        "Student Clashes",
        "Consecutive Penalty",
        "Paper Leak Vulns",
        "Valid?",
    ]
    comp_rows = []
    schedules = {}

    for algo in algorithms:
        scheduler = IntelligentExamScheduler(
            courses, students, rooms, slots_per_day=2, exam_start_date="2026-11-16"
        )
        res = scheduler.generate_schedule(algorithm=algo)
        schedules[algo] = res
        is_valid, _, _ = ScheduleValidator.validate(res, courses, students, rooms, graph)

        comp_rows.append([
            algo.replace("_", " ").title(),
            res.metrics.total_slots_used,
            f"{res.metrics.execution_time_ms:.2f}",
            res.metrics.student_conflict_count,
            res.metrics.consecutive_exam_penalties,
            res.metrics.paper_leak_vulnerabilities,
            "PASS [Zero Clash]" if is_valid else "FAIL",
        ])

    print(format_table(comp_headers, comp_rows))

    # Step 4: Display the Optimal Schedule (Branch and Bound Result)
    best_algo = "branch_and_bound"
    best_schedule = schedules[best_algo]

    print(f"\n[4] OPTIMAL PRODUCTION EXAM TIMETABLE ({best_algo.upper()}):")
    print(f"    * Synchronized Sections: 100% Simultaneous Administration Across Halls")
    print(f"    * Seating Policy: Strict Capacity Enforcement (Allocated Seats <= Hall Capacity)\n")

    tt_headers = [
        "Slot ID",
        "Calendar Date",
        "Clock Time Window",
        "Course Code",
        "Course Title",
        "Level",
        "Headcount",
        "Allocated Halls [Seats/Cap]",
    ]
    tt_rows = []

    course_dict = {c.id: c for c in courses}
    for slot_id in sorted(best_schedule.slot_to_courses.keys()):
        slot_info = best_schedule.time_slots[slot_id]
        c_list = best_schedule.slot_to_courses[slot_id]

        for i, c_id in enumerate(c_list):
            c_obj = course_dict[c_id]

            # Format room seat breakdown
            alloc_details = best_schedule.room_allocation_details.get(c_id, [])
            room_strs = [
                f"{a.room_id} [{a.allocated_seats}/{a.capacity}]"
                for a in alloc_details
            ]
            rooms_display = ", ".join(room_strs) if room_strs else "None"

            slot_label = f"Slot #{slot_id + 1}" if i == 0 else ""
            date_label = slot_info.formatted_date if i == 0 else ""
            time_label = slot_info.time_window if i == 0 else ""
            level_label = f"{c_obj.academic_year} {c_obj.semester.split()[-1]}"

            tt_rows.append([
                slot_label,
                date_label,
                time_label,
                c_obj.code,
                c_obj.name,
                level_label,
                c_obj.student_count,
                rooms_display,
            ])

    print(format_table(tt_headers, tt_rows))

    # Step 5: Rigorous Invariant Validation Audit
    print(f"\n[5] FORMAL 6-INVARIANT CONSTRAINT & INTEGRITY AUDIT:")
    is_valid, errors, val_summary = ScheduleValidator.validate(
        best_schedule, courses, students, rooms, graph
    )
    for k, v in val_summary.items():
        print(f"    - {k:<32}: {v}")

    if not is_valid:
        print("\n[!] Violations Detected:")
        for err in errors:
            print(f"    * {err}")
    else:
        print(f"\n[+] SUCCESS: Verified 100% Conflict-Free Schedule across {len(students)} students and {len(courses)} courses!")
        print(f"    - Strict Room Capacities: SATISFIED (No hall over-allocated)")
        print(f"    - Anti-Paper-Leak Sync  : SATISFIED (Zero cross-session leaks)")
        print(f"    - Calendar Time Windows : SYNTHESIZED ({best_schedule.metrics.calendar_days_spanned} Academic Days)")

    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
