"""
main.py
-------
Main Execution Driver for the Intelligent Exam Scheduling System.

Demonstrates:
1. Conflict Graph Generation & Asymptotic Graph Properties
2. Execution of Heuristic, Exact Backtracking, and Branch & Bound Algorithms
3. Generated Timetable Presentation (Slots, Days, Rooms, Student Counts)
4. Comprehensive Validation Report (Zero-Clash Verification)
"""

import sys
import time

from sample_data import get_academic_dataset
from graph_builder import ConflictGraph
from algorithms.scheduler_engine import IntelligentExamScheduler
from validator import ScheduleValidator


def print_banner():
    print("=" * 80)
    print("   INTELLIGENT EXAM SCHEDULING SYSTEM (DAA CAPSTONE PROJECT)")
    print("   Graph Colouring, Exact Backtracking & Branch and Bound Optimization")
    print("=" * 80)


def format_table(headers, rows):
    """Simple terminal table formatter with proper column padding."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Formatting string
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
    print(f"\n[1] DATASET INITIALIZED:")
    print(f"    - Total Courses (|V|) : {len(courses)}")
    print(f"    - Total Students (|S|): {len(students)}")
    print(f"    - Available Exam Rooms : {len(rooms)}")

    # Step 2: Build & Analyze Conflict Graph
    graph = ConflictGraph.build_from_enrollments(courses, students)
    summary = graph.get_summary_dict()

    print(f"\n[2] CONFLICT GRAPH ANALYSIS (G = (V, E)):")
    print(f"    - Total Vertices (|V|)   : {summary['total_courses']}")
    print(f"    - Total Conflict Edges (|E|): {summary['total_clashes']}")
    print(f"    - Graph Density (D)       : {summary['density']} (Dense/Interconnected)")
    print(f"    - Max Degree Δ(G)         : {summary['max_degree']}")
    print(f"    - Min Degree δ(G)         : {summary['min_degree']}")
    print(f"    - Lower Bound ω(G) [Clique]: {summary['clique_lower_bound_omega']} slots (Theoretical Minimum)")
    print(f"    - Maximal Clique Sample   : {summary['sample_max_clique']}")

    # Step 3: Comparative Evaluation Across Algorithms
    print(f"\n[3] ALGORITHMIC COMPARISON ON CONFLICT GRAPH:")
    algorithms = ["welsh_powell", "dsatur", "backtracking", "branch_and_bound"]
    comp_headers = [
        "Algorithm",
        "Total Slots (k)",
        "Time (ms)",
        "Student Clashes",
        "Consecutive Penalty",
        "Valid?",
    ]
    comp_rows = []
    schedules = {}

    for algo in algorithms:
        scheduler = IntelligentExamScheduler(courses, students, rooms, slots_per_day=2)
        res = scheduler.generate_schedule(algorithm=algo)
        schedules[algo] = res
        is_valid, _, _ = ScheduleValidator.validate(res, courses, students, rooms, graph)

        comp_rows.append([
            algo.replace("_", " ").title(),
            res.metrics.total_slots_used,
            f"{res.metrics.execution_time_ms:.2f}",
            res.metrics.student_conflict_count,
            res.metrics.consecutive_exam_penalties,
            "PASS [Zero Clash]" if is_valid else "FAIL",
        ])

    print(format_table(comp_headers, comp_rows))

    # Step 4: Display the Optimal Schedule (Branch and Bound Result)
    best_algo = "branch_and_bound"
    best_schedule = schedules[best_algo]

    print(f"\n[4] OPTIMAL EXAM TIMETABLE (Generated via {best_algo.upper()}):")
    print(f"    * Slots per day: 2 (Morning: 09:00 - 12:00 | Afternoon: 14:00 - 17:00)\n")

    tt_headers = ["Slot ID", "Day", "Session", "Course Code", "Course Title", "Students", "Allocated Rooms"]
    tt_rows = []

    course_dict = {c.id: c for c in courses}
    for slot_id in sorted(best_schedule.slot_to_courses.keys()):
        day_num = (slot_id // 2) + 1
        session_name = "Morning (09:00 - 12:00)" if (slot_id % 2 == 0) else "Afternoon (14:00 - 17:00)"
        c_list = best_schedule.slot_to_courses[slot_id]

        for i, c_id in enumerate(c_list):
            c_obj = course_dict[c_id]
            rooms_str = ", ".join(best_schedule.room_allocations.get(c_id, ["None"]))
            slot_label = f"Slot #{slot_id + 1}" if i == 0 else ""
            day_label = f"Day {day_num}" if i == 0 else ""
            sess_label = session_name if i == 0 else ""

            tt_rows.append([
                slot_label,
                day_label,
                sess_label,
                c_obj.code,
                c_obj.name,
                c_obj.student_count,
                rooms_str,
            ])

    print(format_table(tt_headers, tt_rows))

    # Step 5: Rigorous Invariant Validation Audit
    print(f"\n[5] FORMAL CONSTRAINT VALIDATION AUDIT:")
    is_valid, errors, val_summary = ScheduleValidator.validate(
        best_schedule, courses, students, rooms, graph
    )
    for k, v in val_summary.items():
        print(f"    - {k:<30}: {v}")

    if not is_valid:
        print("\n[!] Violations Detected:")
        for err in errors:
            print(f"    * {err}")
    else:
        print(f"\n[+] SUCCESS: Verified 100% Conflict-Free Schedule across all {len(students)} students and {len(courses)} courses!")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
