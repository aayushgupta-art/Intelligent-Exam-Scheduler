"""
app.py
------
Streamlit Web Application for Enterprise Intelligent Exam Scheduling System.
Integrates Graph Colouring, CSP Backtracking, and Branch & Bound Optimization with
Real Calendar Dates, Exact Clock Time Windows, Strict Room Capacity BFD, and
Anti-Paper-Leak Section Synchronization.
"""

import streamlit as st
import pandas as pd
import time
import io
import os
from datetime import datetime, date
from typing import List, Dict, Tuple, Set

# Import domain modules
from models import Course, Student, Room, ScheduleResult, RoomSeatAllocation, TimeSlot
from graph_builder import ConflictGraph
from algorithms.scheduler_engine import IntelligentExamScheduler
from sample_data import get_academic_dataset, generate_synthetic_dataset, load_dataset_from_csv
from validator import ScheduleValidator

# Optional visualization libraries
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    HAS_PLOT_LIBS = True
except ImportError:
    HAS_PLOT_LIBS = False


# Set page config
st.set_page_config(
    page_title="Intelligent University Exam Scheduler",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .badge-sync {
        background-color: #EFF6FF;
        color: #1D4ED8;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        border: 1px solid #BFDBFE;
    }
</style>
""", unsafe_allow_html=True)


# ---------------- Helper: CSV Importers & Exporters ----------------

def parse_uploaded_csvs(
    courses_file, students_file, rooms_file
) -> Tuple[List[Course], List[Student], List[Room]]:
    """Parses user-uploaded CSV files into domain entities."""
    courses_df = pd.read_csv(courses_file)
    students_df = pd.read_csv(students_file)
    rooms_df = pd.read_csv(rooms_file)

    courses = [
        Course(
            id=str(row["id"]).strip(),
            code=str(row.get("code", row["id"])).strip(),
            name=str(row.get("name", row["id"])).strip(),
            department=str(row.get("department", "Engineering")).strip(),
            credits=int(row.get("credits", 4)),
            academic_year=str(row.get("academic_year", "Year 3")).strip(),
            semester=str(row.get("semester", "Semester 5")).strip(),
            paper_code=str(row.get("paper_code", row.get("code", row["id"]))).strip(),
        )
        for _, row in courses_df.iterrows()
    ]

    rooms = [
        Room(
            id=str(row["id"]).strip(),
            name=str(row.get("name", row["id"])).strip(),
            capacity=int(row["capacity"]),
            building=str(row.get("building", "Main Block")).strip(),
            room_type=str(row.get("room_type", "Exam Hall")).strip(),
        )
        for _, row in rooms_df.iterrows()
    ]

    students = []
    course_map = {c.id: c for c in courses}
    for _, row in students_df.iterrows():
        s_id = str(row["id"]).strip()
        s_name = str(row.get("name", s_id)).strip()
        branch = str(row.get("branch", "General")).strip()
        academic_year = str(row.get("academic_year", "Year 3")).strip()
        semester = str(row.get("semester", "Semester 5")).strip()
        section = str(row.get("section", "Section A")).strip()
        raw_courses = str(row["enrolled_courses"]).split(";")
        enrolled = {c.strip() for c in raw_courses if c.strip()}
        s_obj = Student(
            id=s_id,
            name=s_name,
            branch=branch,
            academic_year=academic_year,
            semester=semester,
            section=section,
            enrolled_courses=enrolled,
        )
        students.append(s_obj)
        for cid in enrolled:
            if cid in course_map:
                course_map[cid].enrolled_students.add(s_id)

    return courses, students, rooms


def get_csv_templates():
    """Returns downloadable template CSVs for custom data entry."""
    courses_sample = (
        "id,code,name,department,credits,academic_year,semester,paper_code\n"
        "CS301,CS301,Data Structures & Algorithms,Computer Science & Engineering,4,Year 3,Semester 5,P-CS301-COMMON\n"
        "AI301,AI301,Artificial Intelligence & Expert Systems,AI & Machine Learning,4,Year 3,Semester 5,P-AI301-COMMON\n"
        "MA301,MA301,Discrete Mathematical Structures & Graph Theory,Mathematics & Computing,4,Year 3,Semester 5,P-MA301-COMMON"
    )
    students_sample = (
        "id,name,branch,academic_year,semester,section,enrolled_courses\n"
        "2024BCSE001,Aarav Sharma,Computer Science & Engineering,Year 3,Semester 5,Section A,CS301;AI301;MA301\n"
        "2024BAIML001,Aniruddh Prasad,AI & Machine Learning,Year 3,Semester 5,Section A,CS301;AI301;MA301\n"
        "2024BIT001,Chetna Rawal,Information Technology,Year 3,Semester 5,Section A,CS301;MA301"
    )
    rooms_sample = (
        "id,name,capacity,building,room_type\n"
        "AUD_CENTRAL,Dr. APJ Abdul Kalam Central Auditorium,250,Convention Centre,Central Auditorium\n"
        "HALL_CONVOC,Sir C.V. Raman Convocational Exam Hall,180,Academic Block A,Main Examination Hall\n"
        "LAB_TURING_CS,Alan Turing High-Performance Computing Lab,60,CS & AI Complex,Computer Examination Lab"
    )
    return courses_sample, students_sample, rooms_sample


# ---------------- Sidebar Configuration ----------------

with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/university.png", width=60)
    st.title("Exam Cell Control")

    data_source = st.selectbox(
        "📁 Dataset Source",
        [
            "Authentic University Record (12 Courses, 190 Students, 8 Venues)",
            "Load from Local CSV Files (courses.csv, students.csv, rooms.csv)",
            "Synthetic Graph Generator",
            "Upload Custom CSV Files",
        ],
    )

    if data_source == "Authentic University Record (12 Courses, 190 Students, 8 Venues)":
        courses, students, rooms = get_academic_dataset()

    elif data_source == "Load from Local CSV Files (courses.csv, students.csv, rooms.csv)":
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        courses, students, rooms = load_dataset_from_csv(curr_dir)
        st.success(f"Loaded {len(courses)} courses, {len(students)} students, {len(rooms)} venues from local CSVs.")

    elif data_source == "Synthetic Graph Generator":
        st.subheader("Synthetic Parameters")
        num_c = st.slider("Total Courses (|V|)", min_value=6, max_value=40, value=15, step=1)
        num_s = st.slider("Total Students (|S|)", min_value=20, max_value=300, value=100, step=10)
        c_per_s = st.slider("Courses per Student", min_value=2, max_value=6, value=4)
        seed = st.number_input("Random Seed", value=42, step=1)
        courses, students, rooms = generate_synthetic_dataset(num_c, num_s, c_per_s, seed)

    else:
        st.subheader("Upload CSV Files")
        c_file = st.file_uploader("Upload Courses (id, code, name, department, credits)", type=["csv"])
        s_file = st.file_uploader("Upload Students (id, name, branch, enrolled_courses)", type=["csv"])
        r_file = st.file_uploader("Upload Rooms (id, name, capacity, building, room_type)", type=["csv"])

        if c_file and s_file and r_file:
            try:
                courses, students, rooms = parse_uploaded_csvs(c_file, s_file, r_file)
                st.success(f"Loaded {len(courses)} courses, {len(students)} students, {len(rooms)} rooms.")
            except Exception as e:
                st.error(f"Error parsing CSV files: {e}")
                courses, students, rooms = get_academic_dataset()
        else:
            st.info("Upload all 3 CSVs or switch dataset source.")
            courses, students, rooms = get_academic_dataset()

    st.markdown("---")
    st.subheader("📅 Academic Calendar Settings")
    exam_start_val = st.date_input("Exam Block Start Date", value=date(2026, 11, 16))
    exam_start_str = exam_start_val.strftime("%Y-%m-%d")

    slots_per_day = st.radio(
        "Exam Sessions per Day",
        [2, 3],
        index=0,
        format_func=lambda x: "2 Sessions (09:30 AM & 02:00 PM)" if x == 2 else "3 Sessions (09:00 AM, 01:30 PM & 05:30 PM)"
    )

    st.markdown("---")
    st.subheader("⚙️ Optimization Algorithm")
    algo_choice = st.selectbox(
        "Choose Primary Algorithm",
        [
            ("branch_and_bound", "Branch and Bound (Exact Optimal)"),
            ("dsatur", "DSatur (Degree of Saturation Heuristic)"),
            ("welsh_powell", "Welsh-Powell (Largest Degree First)"),
            ("backtracking", "Exact CSP Backtracking (MRV + FC)"),
        ],
        format_func=lambda x: x[1],
    )[0]


# ---------------- Header Banner ----------------

st.markdown('<div class="main-header">Intelligent University Exam Scheduling System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Production Scheduling with Calendar Dates, Clock Timings, Strict Room Bin-Packing & Anti-Paper-Leak Synchronization</div>', unsafe_allow_html=True)


# ---------------- Build Conflict Graph & Execute Scheduler ----------------

graph = ConflictGraph.build_from_enrollments(courses, students)
summary = graph.get_summary_dict()

scheduler = IntelligentExamScheduler(
    courses=courses,
    students=students,
    rooms=rooms,
    slots_per_day=slots_per_day,
    exam_start_date=exam_start_str,
)
active_schedule = scheduler.generate_schedule(algorithm=algo_choice)
is_valid, error_log, audit_summary = ScheduleValidator.validate(active_schedule, courses, students, rooms, graph)


# ---------------- Top Metrics Dashboard ----------------

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="Total Courses (|V|)",
        value=len(courses),
        help="Number of academic course vertices in the conflict graph",
    )
with col2:
    st.metric(
        label="Total Students (|S|)",
        value=len(students),
        delta=f"Clashes: {graph.edge_count} Edges",
        help="Enrolled students across academic branches",
    )
with col3:
    st.metric(
        label="Exam Slots (k)",
        value=active_schedule.metrics.total_slots_used,
        delta=f"Lower Bound ω: {summary['clique_lower_bound_omega']}",
        help="Total time slots required (Chromatic Number)",
    )
with col4:
    st.metric(
        label="Calendar Duration",
        value=f"{active_schedule.metrics.calendar_days_spanned} Days",
        delta=f"From {exam_start_val.strftime('%d %b %Y')}",
        help="Academic exam period duration",
    )
with col5:
    status_label = "✅ 100% Conflict-Free" if is_valid else "❌ Conflicts Detected"
    st.metric(
        label="Validation Status",
        value="PASSED" if is_valid else "FAILED",
        delta=status_label,
    )


# ---------------- Main Navigation Tabs ----------------

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📅 Generated Timetable",
    "🕸️ Conflict Graph & Chromatic Analytics",
    "⚡ Multi-Algorithm Comparison",
    "🛡️ Formal 6-Invariant Audit",
    "📋 Exam Manifest & Seating Reports",
    "📁 Student Lookup & CSV Hub",
])


# ==================== TAB 1: GENERATED TIMETABLE ====================
with tab1:
    st.subheader(f"Generated University Exam Timetable ({algo_choice.replace('_', ' ').title()})")

    # Build DataFrame for Timetable
    timetable_data = []
    course_dict = {c.id: c for c in courses}

    for slot_id in sorted(active_schedule.slot_to_courses.keys()):
        slot_info = active_schedule.time_slots.get(slot_id)
        if not slot_info:
            continue

        for c_id in active_schedule.slot_to_courses[slot_id]:
            c_obj = course_dict[c_id]
            allocations = active_schedule.room_allocation_details.get(c_id, [])
            room_detail_strs = [
                f"{a.room_name} ({a.room_id}): {a.allocated_seats}/{a.capacity} seats"
                for a in allocations
            ]
            assigned_rooms_str = " | ".join(room_detail_strs) if room_detail_strs else "None"

            timetable_data.append({
                "Slot ID": f"Slot #{slot_id + 1}",
                "Calendar Date": slot_info.formatted_date,
                "Time Window": slot_info.time_window,
                "Session": slot_info.session_name,
                "Course Code": c_obj.code,
                "Course Title": c_obj.name,
                "Department": getattr(c_obj, "department", "Engineering"),
                "Academic Level": f"{getattr(c_obj, 'academic_year', 'Year 3')} ({getattr(c_obj, 'semester', 'Sem 5')})",
                "Paper Code": getattr(c_obj, "paper_code", c_obj.code),
                "Headcount": c_obj.student_count,
                "Allocated Exam Hall(s) & Capacity": assigned_rooms_str,
            })

    tt_df = pd.DataFrame(timetable_data)

    # Interactive Filters
    col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
    with col_f1:
        date_options = tt_df["Calendar Date"].unique().tolist()
        selected_dates = st.multiselect("Filter by Exam Date", options=date_options, default=date_options)
    with col_f2:
        dept_options = tt_df["Department"].unique().tolist()
        selected_depts = st.multiselect("Filter by Department", options=dept_options, default=dept_options)
    with col_f3:
        search_query = st.text_input("Search Course Code / Title / Paper", "")

    filtered_df = tt_df[
        (tt_df["Calendar Date"].isin(selected_dates)) &
        (tt_df["Department"].isin(selected_depts))
    ]
    if search_query:
        filtered_df = filtered_df[
            filtered_df["Course Code"].str.contains(search_query, case=False) |
            filtered_df["Course Title"].str.contains(search_query, case=False) |
            filtered_df["Paper Code"].str.contains(search_query, case=False)
        ]

    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    # Download Buttons
    csv_buffer = io.StringIO()
    tt_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📥 Download Complete Master Timetable as CSV",
        data=csv_buffer.getvalue(),
        file_name="university_exam_master_timetable.csv",
        mime="text/csv",
    )


# ==================== TAB 2: CONFLICT GRAPH & CHROMATIC ANALYTICS ====================
with tab2:
    st.subheader("Conflict Graph Formulation & Chromatic Analytics")

    col_g1, col_g2 = st.columns([1, 1])

    with col_g1:
        st.markdown("#### Graph Theoretical Properties")
        st.write(f"- **Total Course Vertices ($|V|$):** `{summary['total_courses']}`")
        st.write(f"- **Total Conflict Clashes ($|E|$):** `{summary['total_clashes']}`")
        st.write(f"- **Graph Density ($D = \\frac{{2|E|}}{{|V|(|V|-1)}}$):** `{summary['density']}`")
        st.write(f"- **Max Degree $\\Delta(G)$:** `{summary['max_degree']}`")
        st.write(f"- **Min Degree $\\delta(G)$:** `{summary['min_degree']}`")
        st.write(f"- **Maximal Clique Lower Bound $\\omega(G)$:** `{summary['clique_lower_bound_omega']}` slots")
        st.write(f"- **Identified Max Clique:** `{', '.join(summary['sample_max_clique'])}`")
        st.write(f"- **Chromatic Number Achieved $\\chi(G)$:** `{active_schedule.metrics.total_slots_used}` slots")

        if summary['clique_lower_bound_omega'] == active_schedule.metrics.total_slots_used:
            st.success("🎯 **Optimality Certified:** $\\omega(G) = \\chi(G)$ (Exact Theoretical Minimum Achieved!)")

    with col_g2:
        st.markdown("#### Visual Conflict Graph")
        if HAS_PLOT_LIBS:
            fig, ax = plt.subplots(figsize=(7, 5))
            G = nx.Graph()
            for u in graph.vertices:
                G.add_node(u)
            for (u, v), w in graph.edge_weights.items():
                G.add_edge(u, v, weight=w)

            # Assign node colors based on time slot
            color_map = []
            palette = [
                "#3B82F6", "#10B981", "#F59E0B", "#EF4444",
                "#8B5CF6", "#EC4899", "#14B8A6", "#F97316",
                "#6366F1", "#84CC16", "#06B6D4", "#D946EF"
            ]
            for node in G.nodes():
                slot = active_schedule.course_to_slot.get(node, 0)
                color_map.append(palette[slot % len(palette)])

            pos = nx.spring_layout(G, seed=42)
            nx.draw_networkx_nodes(G, pos, node_color=color_map, node_size=650, ax=ax)
            nx.draw_networkx_edges(G, pos, alpha=0.3, ax=ax)
            nx.draw_networkx_labels(G, pos, font_size=8, font_family="sans-serif", ax=ax)
            ax.set_title("Course Conflict Graph (Colors = Exam Time Slots)", fontsize=10)
            ax.axis("off")
            st.pyplot(fig)
        else:
            st.info("Install `networkx` and `matplotlib` for interactive graph rendering.")


# ==================== TAB 3: ALGORITHM COMPARISON ====================
with tab3:
    st.subheader("Comparative Benchmark Across All 4 Optimization Algorithms")
    st.markdown("Rigorous benchmark of **Welsh-Powell**, **DSatur**, **Backtracking CSP (MRV+FC)**, and **Branch & Bound** on the current dataset:")

    algos = ["welsh_powell", "dsatur", "backtracking", "branch_and_bound"]
    comp_records = []

    for a in algos:
        sched = scheduler.generate_schedule(algorithm=a)
        is_v, _, _ = ScheduleValidator.validate(sched, courses, students, rooms, graph)
        comp_records.append({
            "Algorithm": a.replace("_", " ").title(),
            "Total Slots (k)": sched.metrics.total_slots_used,
            "Execution Time (ms)": sched.metrics.execution_time_ms,
            "Student Clashes": sched.metrics.student_conflict_count,
            "Consecutive Exam Fatigue": sched.metrics.consecutive_exam_penalties,
            "Same-Day Fatigue": sched.metrics.same_day_exam_penalties,
            "Paper Leak Risk": sched.metrics.paper_leak_vulnerabilities,
            "Status": "PASSED" if is_v else "FAILED",
        })

    comp_df = pd.DataFrame(comp_records)
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("#### Execution Time Comparison (ms)")
        st.bar_chart(comp_df.set_index("Algorithm")["Execution Time (ms)"])
    with col_c2:
        st.markdown("#### Slots Required (k = Chromatic Number)")
        st.bar_chart(comp_df.set_index("Algorithm")["Total Slots (k)"])


# ==================== TAB 4: FORMAL 6-INVARIANT AUDIT ====================
with tab4:
    st.subheader("Formal 6-Invariant Integrity & Security Audit")
    st.markdown("Mathematical verification verifying all hard constraints, room capacity invariants, and anti-paper-leak synchronization:")

    audit_col1, audit_col2 = st.columns(2)

    with audit_col1:
        st.markdown("#### Verification Audit Checklist")
        st.write(f"1. **Completeness (All Courses Scheduled):** {'✅ PASSED' if audit_summary['total_courses_audited'] == len(courses) else '❌ FAILED'}")
        st.write(f"2. **Conflict-Free Invariant (Student Clashes):** `0 Violations` ✅" if audit_summary['student_clashes'] == 0 else f"`{audit_summary['student_clashes']} Clashes` ❌")
        st.write(f"3. **Graph Adjacency Invariant:** `0 Violations` ✅" if audit_summary['graph_edge_violations'] == 0 else f"`{audit_summary['graph_edge_violations']} Violations` ❌")
        st.write(f"4. **Room Double-Booking Check:** `0 Conflicts` ✅" if audit_summary['room_double_bookings'] == 0 else f"`{audit_summary['room_double_bookings']} Conflicts` ❌")
        st.write(f"5. **Strict Room Capacity Invariant:** `0 Over-allocations` ✅" if audit_summary['room_overallocations'] == 0 else f"`{audit_summary['room_overallocations']} Over-Allocations` ❌")
        st.write(f"6. **Anti-Paper-Leak Common Paper Sync:** `100% Synchronized (0 Leak Risks)` ✅" if audit_summary['paper_leak_vulnerabilities'] == 0 else f"`{audit_summary['paper_leak_vulnerabilities']} Vulnerabilities` ❌")

    with audit_col2:
        st.markdown("#### Audit Outcome")
        if is_valid:
            st.success("🎉 **ENTERPRISE INTEGRITY CERTIFICATE ISSUED:** The generated schedule strictly adheres to all 6 hard invariants. No student has concurrent exams, all hall capacities are respected, and all common examination papers are 100% synchronized across parallel sections.")
        else:
            st.error("⚠️ Violations detected during validation audit:")
            for err in error_log:
                st.write(f"- {err}")


# ==================== TAB 5: EXAM MANIFEST & SEATING REPORTS ====================
with tab5:
    st.subheader("📋 Room-Wise Seating Allocation Matrix & Attendance Manifests")
    st.markdown("Official examination room attendance sheets showing PRN, student name, course code, room name, and invigilator signature columns.")

    # Build seating allocator
    from seating_allocator import SeatingAllocator
    allocator = SeatingAllocator(courses, students, rooms, active_schedule)
    room_manifests = allocator.generate_room_manifests()

    # Display manifest statistics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric(label="Total Students Seated", value=active_schedule.metrics.total_seats_allocated)
    with col_m2:
        st.metric(label="Total Rooms Used", value=len(room_manifests))
    with col_m3:
        st.metric(label="Multi-Hall Splits", value=active_schedule.metrics.multi_room_splits_count)
    with col_m4:
        st.metric(label="Anti-Paper-Leak Sync", value="✅ SYNCHRONIZED" if active_schedule.metrics.paper_leak_vulnerabilities == 0 else "❌ VULNERABLE")

    # Room Manifest Selection
    st.markdown("---")
    st.markdown("#### 📄 Room Attendance Manifest Viewer")
    manifest_keys = list(room_manifests.keys())
    if manifest_keys:
        manifest_options = [f"{m.room_name} ({m.room_id}) - {m.formatted_date} - {m.time_window}" for m in room_manifests.values()]
        selected_manifest_idx = st.selectbox(
            "Select Examination Room & Session",
            options=range(len(manifest_options)),
            format_func=lambda i: manifest_options[i],
        )
        selected_key = manifest_keys[selected_manifest_idx]
        selected_manifest = room_manifests[selected_key]

        # Manifest header
        col_h1, col_h2 = st.columns([2, 1])
        with col_h1:
            st.info(f"**Room:** {selected_manifest.room_name} | **Building:** {next((r.building for r in rooms if r.id == selected_manifest.room_id), 'N/A')}")
        with col_h2:
            st.info(f"**Date:** {selected_manifest.calendar_date} | **Time:** {selected_manifest.time_window}")

        st.write(f"**Session:** {selected_manifest.session_name} | **Total Students:** {selected_manifest.total_students} | **Courses:** {', '.join(selected_manifest.course_codes)}")

        # Build manifest DataFrame
        manifest_rows = []
        for row in selected_manifest.student_rows:
            manifest_rows.append({
                "Seat Label": row.seat_label,
                "Seat No.": row.seat_number,
                "PRN": row.student_id,
                "Student Name": row.student_name,
                "Branch": row.branch,
                "Academic Year": row.academic_year,
                "Course Code": row.course_code,
                "Course Title": row.course_title,
                "Invigilator Signature": "",
            })

        manifest_df = pd.DataFrame(manifest_rows)

        # Search filter for examiners to locate student quickly
        search_query_manifest = st.text_input(
            "🔍 Search Student by Name or PRN (Instant Filter)",
            "",
            key="manifest_search",
            help="Type a student's name or PRN (e.g., 'Aarav Sharma' or '2024BCSE001') to filter the seating manifest instantly.",
        )
        if search_query_manifest:
            q = search_query_manifest.lower()
            filtered_df = manifest_df[
                manifest_df["Student Name"].str.lower().str.contains(q, na=False) |
                manifest_df["PRN"].str.lower().str.contains(q, na=False)
            ]
            filtered_df = filtered_df.sort_values("Seat No.")
            if len(filtered_df) == 0:
                st.info("No matching student found for this manifest.")
            else:
                st.success(f"Found {len(filtered_df)} matching seat(s) for '{search_query_manifest}'")
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(manifest_df, use_container_width=True, hide_index=True)

        # Download manifest CSV
        csv_buffer = io.StringIO()
        manifest_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label=f"📥 Download Room Manifest: {selected_manifest.room_name} (CSV)",
            data=csv_buffer.getvalue(),
            file_name=f"room_manifest_{selected_manifest.room_id}_{selected_manifest.calendar_date.replace('-', '_')}.csv",
            mime="text/csv",
        )

    st.markdown("---")
    st.markdown("#### 🎫 Individual Student Admit Cards")
    student_cards = allocator.generate_student_admit_cards()

    if student_cards:
        student_lookup = {s.id: s for s in students}
        card_options = [f"{student_lookup[sid].name} ({sid}) - {student_lookup[sid].branch}" for sid in student_cards.keys()]
        selected_card_idx = st.selectbox(
            "Select Student to Generate Admit Card",
            options=range(len(card_options)),
            format_func=lambda i: card_options[i],
            key="admit_card_selector",
        )
        selected_sid = list(student_cards.keys())[selected_card_idx]
        selected_student = student_lookup[selected_sid]
        card_rows = student_cards[selected_sid]

        st.write(f"**Student:** {selected_student.name} | **PRN:** {selected_student.id} | **Branch:** {selected_student.branch}")
        st.write(f"**Academic Level:** {selected_student.academic_year} | {selected_student.semester} | {selected_student.section}")

        admit_rows = []
        for assignment in card_rows:
            admit_rows.append({
                "Course Code": assignment.course_code,
                "Course Title": assignment.course_title,
                "Date": assignment.calendar_date,
                "Time Window": assignment.time_window,
                "Session": assignment.session_name,
                "Room Name": assignment.room_name,
                "Room ID": assignment.room_id,
                "Seat Label": assignment.seat_label,
            })

        admit_df = pd.DataFrame(admit_rows)
        st.dataframe(admit_df, use_container_width=True, hide_index=True)

        # Download admit card as official PDF
        from hall_ticket_pdf import generate_official_hall_ticket_pdf
        student_lookup_for_pdf = {s.id: s for s in students}
        pdf_bytes = generate_official_hall_ticket_pdf(
            student_lookup_for_pdf[selected_sid],
            card_rows,
        )
        st.download_button(
            label=f"📥 Download Official Hall Ticket (PDF) — {selected_student.name}",
            data=pdf_bytes,
            file_name=f"hall_ticket_{selected_student.id}.pdf",
            mime="application/pdf",
        )


# ==================== TAB 6: STUDENT LOOKUP & CSV HUB ====================
with tab6:
    st.subheader("Personalized Student Exam Pass & Academic CSV Repository")

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.markdown("#### Individual Student Exam Hall Ticket / Pass")
        student_display_list = [
            f"{s.name} ({s.id}) - {getattr(s, 'branch', 'Engg')} [{getattr(s, 'section', 'Sec A')}]"
            for s in students
        ]
        selected_s_str = st.selectbox("Select Student to View Hall Ticket", student_display_list)

        selected_s_id = selected_s_str.split("(")[1].split(")")[0].strip()
        selected_student = next((s for s in students if s.id == selected_s_id), None)

        if selected_student:
            st.write(f"**Student Name:** {selected_student.name} (`{selected_student.id}`)")
            st.write(f"**Branch / Cohort:** {getattr(selected_student, 'branch', 'Engineering')}")
            st.write(f"**Academic Level:** {getattr(selected_student, 'academic_year', 'Year 3')} | {getattr(selected_student, 'semester', 'Semester 5')} | {getattr(selected_student, 'section', 'Section A')}")
            st.write(f"**Enrolled Courses ({len(selected_student.enrolled_courses)}):** {', '.join(sorted(selected_student.enrolled_courses))}")

            s_exams = []
            for cid in selected_student.enrolled_courses:
                if cid in active_schedule.course_to_slot:
                    slot = active_schedule.course_to_slot[cid]
                    slot_meta = active_schedule.time_slots.get(slot)
                    allocations = active_schedule.room_allocation_details.get(cid, [])
                    room_str = ", ".join(f"{a.room_name} ({a.room_id})" for a in allocations) if allocations else "TBD"

                    s_exams.append({
                        "Course Code": cid,
                        "Course Title": course_dict[cid].name,
                        "Credits": getattr(course_dict[cid], "credits", 4),
                        "Date": slot_meta.formatted_date if slot_meta else f"Slot {slot+1}",
                        "Time Window": slot_meta.time_window if slot_meta else "TBD",
                        "Session": slot_meta.session_name if slot_meta else f"Slot {slot+1}",
                        "Assigned Hall(s)": room_str,
                    })
            s_exams_df = pd.DataFrame(s_exams)
            st.dataframe(s_exams_df, hide_index=True, use_container_width=True)

    with col_s2:
        st.markdown("#### Live Academic CSV Repository")
        st.write("Download the active university examination records directly from the database:")

        active_courses_df = pd.DataFrame([
            {
                "id": c.id,
                "code": c.code,
                "name": c.name,
                "department": getattr(c, "department", "Engineering"),
                "credits": getattr(c, "credits", 4),
                "academic_year": getattr(c, "academic_year", "Year 3"),
                "semester": getattr(c, "semester", "Semester 5"),
                "paper_code": getattr(c, "paper_code", c.code),
            }
            for c in courses
        ])
        active_students_df = pd.DataFrame([
            {
                "id": s.id,
                "name": s.name,
                "branch": getattr(s, "branch", "General"),
                "academic_year": getattr(s, "academic_year", "Year 3"),
                "semester": getattr(s, "semester", "Semester 5"),
                "section": getattr(s, "section", "Section A"),
                "enrolled_courses": ";".join(sorted(s.enrolled_courses)),
            }
            for s in students
        ])
        active_rooms_df = pd.DataFrame([
            {
                "id": r.id,
                "name": r.name,
                "capacity": r.capacity,
                "building": r.building,
                "room_type": getattr(r, "room_type", "Exam Hall"),
            }
            for r in rooms
        ])

        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(
                "📥 courses.csv",
                active_courses_df.to_csv(index=False),
                "courses.csv",
                "text/csv",
            )
        with c2:
            st.download_button(
                "📥 students.csv",
                active_students_df.to_csv(index=False),
                "students.csv",
                "text/csv",
            )
        with c3:
            st.download_button(
                "📥 rooms.csv",
                active_rooms_df.to_csv(index=False),
                "rooms.csv",
                "text/csv",
            )

        st.markdown("---")
        st.markdown("#### Download Schema Templates")
        st.write("Use these schemas to format custom university datasets:")
        c_csv, s_csv, r_csv = get_csv_templates()

        t1, t2, t3 = st.columns(3)
        with t1:
            st.download_button("📄 courses_template.csv", c_csv, "courses_template.csv", "text/csv")
        with t2:
            st.download_button("📄 students_template.csv", s_csv, "students_template.csv", "text/csv")
        with t3:
            st.download_button("📄 rooms_template.csv", r_csv, "rooms_template.csv", "text/csv")
