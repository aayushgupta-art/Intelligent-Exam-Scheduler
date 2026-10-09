"""
app.py
------
Streamlit Web Application for Intelligent Exam Scheduling System.
Integrates Graph Colouring, CSP Backtracking, and Branch & Bound Optimization.
"""

import streamlit as st
import pandas as pd
import time
import io
from typing import List, Dict, Tuple, Set

# Import domain modules
from models import Course, Student, Room, ScheduleResult
from graph_builder import ConflictGraph
from algorithms.scheduler_engine import IntelligentExamScheduler
from sample_data import get_academic_dataset, generate_synthetic_dataset
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
    page_title="Intelligent Exam Scheduler (DAA)",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px;
        text-align: center;
    }
    .badge-success {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .badge-fail {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.9rem;
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
        raw_courses = str(row["enrolled_courses"]).split(";")
        enrolled = {c.strip() for c in raw_courses if c.strip()}
        s_obj = Student(id=s_id, name=s_name, branch=branch, enrolled_courses=enrolled)
        students.append(s_obj)
        for cid in enrolled:
            if cid in course_map:
                course_map[cid].enrolled_students.add(s_id)

    return courses, students, rooms


def get_csv_templates():
    """Returns downloadable template CSVs for custom data entry."""
    courses_sample = (
        "id,code,name,department,credits\n"
        "CS301,CS301,Data Structures & Algorithms,Computer Science & Engineering,4\n"
        "AI301,AI301,Artificial Intelligence & Expert Systems,AI & Machine Learning,4\n"
        "MA301,MA301,Discrete Mathematical Structures & Graph Theory,Mathematics & Computing,4"
    )
    students_sample = (
        "id,name,branch,enrolled_courses\n"
        "2024BCSE001,Aarav Sharma,Computer Science & Engineering,CS301;AI301;MA301\n"
        "2024BAIML001,Aniruddh Prasad,AI & Machine Learning,CS301;AI301;MA301\n"
        "2024BIT001,Chetna Rawal,Information Technology,CS301;MA301"
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
    st.image("https://img.icons8.com/color/96/000000/university.png", width=64)
    st.title("Scheduler Config")

    data_source = st.selectbox(
        "📁 Dataset Source",
        [
            "Authentic University Record (12 Courses, 190 Students, 8 Venues)",
            "Synthetic Graph Generator",
            "Upload Custom CSV Files",
        ],
    )

    if data_source == "Authentic University Record (12 Courses, 190 Students, 8 Venues)":
        courses, students, rooms = get_academic_dataset()

    elif data_source == "Synthetic Graph Generator":
        st.subheader("Synthetic Parameters")
        num_c = st.slider("Total Courses (|V|)", min_value=6, max_value=40, value=15, step=1)
        num_s = st.slider("Total Students (|S|)", min_value=20, max_value=300, value=80, step=10)
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
    st.subheader("⚙️ Algorithm Selection")
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

    slots_per_day = st.radio("Exam Slots per Day", [2, 3], index=0, format_func=lambda x: f"{x} Sessions/Day")


# ---------------- Header Banner ----------------

st.markdown('<div class="main-header">Intelligent University Exam Scheduling System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Graph Colouring, Backtracking Constraint Satisfaction & Branch-and-Bound Optimization (DAA Capstone)</div>', unsafe_allow_html=True)


# ---------------- Build Conflict Graph & Execute Scheduler ----------------

graph = ConflictGraph.build_from_enrollments(courses, students)
summary = graph.get_summary_dict()

scheduler = IntelligentExamScheduler(courses, students, rooms, slots_per_day=slots_per_day)
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
        label="Conflict Edges (|E|)",
        value=graph.edge_count,
        delta=f"Density: {graph.density():.2f}",
        help="Pairs of courses sharing enrolled students",
    )
with col3:
    st.metric(
        label="Slots Used (k)",
        value=active_schedule.metrics.total_slots_used,
        delta=f"Lower Bound ω: {summary['clique_lower_bound_omega']}",
        help="Minimum chromatic number slots required",
    )
with col4:
    st.metric(
        label="Execution Time",
        value=f"{active_schedule.metrics.execution_time_ms:.1f} ms",
        help="Time taken by the optimization algorithm",
    )
with col5:
    status_label = "✅ 100% Conflict-Free" if is_valid else "❌ Conflicts Detected"
    st.metric(
        label="Validation Status",
        value="PASSED" if is_valid else "FAILED",
        delta=status_label,
    )


# ---------------- Main Navigation Tabs ----------------

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 Generated Timetable",
    "🕸️ Conflict Graph & Chromatic Analytics",
    "⚡ Multi-Algorithm Comparison",
    "🛡️ Formal Invariant Audit",
    "📁 CSV Templates & Student Lookup",
])


# ==================== TAB 1: GENERATED TIMETABLE ====================
with tab1:
    st.subheader(f"Generated Conflict-Free Exam Timetable ({algo_choice.replace('_', ' ').title()})")

    # Build DataFrame for Timetable
    timetable_data = []
    course_dict = {c.id: c for c in courses}

    for slot_id in sorted(active_schedule.slot_to_courses.keys()):
        day_num = (slot_id // slots_per_day) + 1
        sess_num = (slot_id % slots_per_day) + 1
        session_label = f"Session {sess_num} (Morning)" if sess_num == 1 else f"Session {sess_num} (Afternoon)"

        for c_id in active_schedule.slot_to_courses[slot_id]:
            c_obj = course_dict[c_id]
            assigned_rooms = ", ".join(active_schedule.room_allocations.get(c_id, ["None"]))
            timetable_data.append({
                "Slot ID": f"Slot #{slot_id + 1}",
                "Day": f"Day {day_num}",
                "Session": session_label,
                "Course Code": c_obj.code,
                "Course Title": c_obj.name,
                "Enrolled Students": c_obj.student_count,
                "Allocated Room(s)": assigned_rooms,
            })

    tt_df = pd.DataFrame(timetable_data)

    # Interactive Filter by Day / Slot
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        selected_day = st.multiselect("Filter by Day", options=tt_df["Day"].unique(), default=tt_df["Day"].unique())
    with col_f2:
        search_query = st.text_input("Search Course Code or Title", "")

    filtered_df = tt_df[tt_df["Day"].isin(selected_day)]
    if search_query:
        filtered_df = filtered_df[
            filtered_df["Course Code"].str.contains(search_query, case=False) |
            filtered_df["Course Title"].str.contains(search_query, case=False)
        ]

    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    # Download Buttons
    csv_buffer = io.StringIO()
    tt_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📥 Download Timetable as CSV",
        data=csv_buffer.getvalue(),
        file_name="exam_schedule_optimized.csv",
        mime="text/csv",
    )


# ==================== TAB 2: CONFLICT GRAPH & CHROMATIC ANALYTICS ====================
with tab2:
    st.subheader("Conflict Graph Formulation & Chromatic Analysis")

    col_g1, col_g2 = st.columns([1, 1])

    with col_g1:
        st.markdown("#### Graph Theoretical Metrics")
        st.write(f"- **Total Course Vertices ($|V|$):** `{summary['total_courses']}`")
        st.write(f"- **Total Conflict Clashes ($|E|$):** `{summary['total_clashes']}`")
        st.write(f"- **Graph Density ($D = \\frac{{2|E|}}{{|V|(|V|-1)}}$):** `{summary['density']}`")
        st.write(f"- **Max Degree $\\Delta(G)$:** `{summary['max_degree']}`")
        st.write(f"- **Min Degree $\\delta(G)$:** `{summary['min_degree']}`")
        st.write(f"- **Maximal Clique Lower Bound $\\omega(G)$:** `{summary['clique_lower_bound_omega']}` slots")
        st.write(f"- **Identified Max Clique:** `{', '.join(summary['sample_max_clique'])}`")
        st.write(f"- **Achieved Chromatic Number $\\chi(G)$:** `{active_schedule.metrics.total_slots_used}` slots")

        if summary['clique_lower_bound_omega'] == active_schedule.metrics.total_slots_used:
            st.success("🎯 **Optimality Certified:** $\\omega(G) = \\chi(G)$ (Theoretical Minimum Achieved!)")

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
            nx.draw_networkx_nodes(G, pos, node_color=color_map, node_size=600, ax=ax)
            nx.draw_networkx_edges(G, pos, alpha=0.3, ax=ax)
            nx.draw_networkx_labels(G, pos, font_size=8, font_family="sans-serif", ax=ax)
            ax.set_title(f"Conflict Graph (Colors = Time Slots)", fontsize=10)
            ax.axis("off")
            st.pyplot(fig)
        else:
            st.info("Install `networkx` and `matplotlib` for interactive graph rendering.")


# ==================== TAB 3: ALGORITHM COMPARISON ====================
with tab3:
    st.subheader("Comparative Evaluation Across All 4 Optimization Algorithms")
    st.markdown("Evaluates **Welsh-Powell**, **DSatur**, **Exact CSP Backtracking**, and **Branch & Bound** on the current dataset:")

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
            "Slot Variance": sched.metrics.slot_distribution_variance,
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


# ==================== TAB 4: FORMAL INVARIANT AUDIT ====================
with tab4:
    st.subheader("Formal Constraint Verification & Invariant Audit")
    st.markdown("Automated integrity checks verifying that hard mathematical and physical constraints are satisfied without exception:")

    audit_col1, audit_col2 = st.columns(2)

    with audit_col1:
        st.markdown("#### Audit Checklist")
        st.write(f"- **Completeness (All Courses Scheduled):** {'✅ PASSED' if audit_summary['total_courses_audited'] == len(courses) else '❌ FAILED'}")
        st.write(f"- **Conflict-Free Invariant (Student Clashes):** `0 Violations` ✅" if audit_summary['student_clashes'] == 0 else f"`{audit_summary['student_clashes']} Clashes` ❌")
        st.write(f"- **Graph Adjacency Invariant:** `0 Violations` ✅" if audit_summary['graph_edge_violations'] == 0 else f"`{audit_summary['graph_edge_violations']} Violations` ❌")
        st.write(f"- **Room Double-Booking Check:** `0 Conflicts` ✅" if audit_summary['room_double_bookings'] == 0 else f"`{audit_summary['room_double_bookings']} Conflicts` ❌")
        st.write(f"- **Room Capacity Invariant:** `0 Shortages` ✅" if audit_summary['room_capacity_shortages'] == 0 else f"`{audit_summary['room_capacity_shortages']} Shortages` ❌")

    with audit_col2:
        st.markdown("#### Audit Outcome")
        if is_valid:
            st.success("🎉 **VERIFICATION CERTIFICATE:** The generated timetable strictly satisfies all 5 hard invariants. Zero students have overlapping exams and all physical hall capacities are respected.")
        else:
            st.error("⚠️ Violations detected during validation audit:")
            for err in error_log:
                st.write(f"- {err}")


# ==================== TAB 5: STUDENT LOOKUP & TEMPLATES ====================
with tab5:
    st.subheader("Personalized Student Schedule Lookup & CSV Repository")

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.markdown("#### Individual Student Exam Lookup")
        student_names = [f"{s.name} ({s.id}) - {getattr(s, 'branch', 'Engineering')}" for s in students]
        selected_s_str = st.selectbox("Select Student to View Individual Timetable", student_names)

        selected_s_id = selected_s_str.split("(")[1].split(")")[0].strip()
        selected_student = next((s for s in students if s.id == selected_s_id), None)

        if selected_student:
            st.write(f"**Student Name:** {selected_student.name} (`{selected_student.id}`)")
            st.write(f"**Academic Branch:** {getattr(selected_student, 'branch', 'Engineering')}")
            st.write(f"**Enrolled Courses ({len(selected_student.enrolled_courses)}):** {', '.join(sorted(selected_student.enrolled_courses))}")

            s_exams = []
            for cid in selected_student.enrolled_courses:
                if cid in active_schedule.course_to_slot:
                    slot = active_schedule.course_to_slot[cid]
                    day = (slot // slots_per_day) + 1
                    sess = (slot % slots_per_day) + 1
                    s_exams.append({
                        "Course Code": cid,
                        "Course Title": course_dict[cid].name,
                        "Credits": getattr(course_dict[cid], "credits", 4),
                        "Day": f"Day {day}",
                        "Session": f"Session {sess}",
                        "Slot": f"Slot #{slot + 1}",
                        "Assigned Room(s)": ", ".join(active_schedule.room_allocations.get(cid, [])),
                    })
            s_exams_df = pd.DataFrame(s_exams).sort_values("Slot")
            st.dataframe(s_exams_df, hide_index=True, use_container_width=True)

    with col_s2:
        st.markdown("#### Download Authentic University CSV Records")
        st.write("Download the current active university dataset records (courses.csv, students.csv, rooms.csv):")

        # Prepare active CSV data
        active_courses_df = pd.DataFrame([
            {
                "id": c.id,
                "code": c.code,
                "name": c.name,
                "department": getattr(c, "department", "Engineering"),
                "credits": getattr(c, "credits", 4),
            }
            for c in courses
        ])
        active_students_df = pd.DataFrame([
            {
                "id": s.id,
                "name": s.name,
                "branch": getattr(s, "branch", "General"),
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
        st.markdown("#### Blank / Template CSV Format")
        st.write("Use these template schemas to format external data for uploading:")
        c_csv, s_csv, r_csv = get_csv_templates()

        t1, t2, t3 = st.columns(3)
        with t1:
            st.download_button("📄 courses_template.csv", c_csv, "courses_template.csv", "text/csv")
        with t2:
            st.download_button("📄 students_template.csv", s_csv, "students_template.csv", "text/csv")
        with t3:
            st.download_button("📄 rooms_template.csv", r_csv, "rooms_template.csv", "text/csv")
