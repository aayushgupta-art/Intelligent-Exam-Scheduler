# Intelligent Exam Scheduling Using Graph Colouring, Backtracking and Optimization Techniques

**Course:** Design and Analysis of Algorithms (DAA)  
**Specialization:** Computer Science and Engineering (Artificial Intelligence & Machine Learning)  
**Project Directory:** `C:\Users\ADMIN\OneDrive\Desktop\cloude\DAA PROJECT`

---

## 1. Executive Summary & Problem Formulation

University examination timetabling is a notoriously complex combinatorial optimization problem classified as **NP-Hard**. Given a set of courses with overlapping student enrollments, limited physical examination venues, and strict time windows, the objective is to generate an optimal, conflict-free schedule.

This project implements an end-to-end algorithmic framework integrating:
1. **Graph Theory & Conflict Graph Modeling:** Formulating courses as vertices and enrollment clashes as weighted edges.
2. **Greedy Heuristics (Welsh-Powell & DSatur):** Constructing fast polynomial-time initial approximations and establishing an upper bound ($U = \chi_{\text{heuristic}}(G)$).
3. **Constraint Satisfaction Problem (CSP) Backtracking:** Implementing exact backtracking equipped with **Minimum Remaining Values (MRV)**, **Degree Heuristic**, and **Forward Checking (FC)**.
4. **Branch and Bound Optimization:** Pruning exponential search subtrees using the maximal clique lower bound ($\omega(G) \le \chi(G)$) and symmetry-breaking constraints.
5. **Multi-Capacity Room Allocation (Bin Packing):** Allocating exam halls to simultaneous courses using **Best-Fit Decreasing (BFD)**.
6. **Soft-Constraint Fatigue Minimization:** Permuting time slots to minimize consecutive and same-day student exam fatigue.

---

## 2. Mathematical Modeling & Formal Definitions

### 2.1 Graph Formulation
Let $G = (V, E)$ be an undirected, weighted conflict graph:
* **Vertex Set $V$:** $V = \{c_1, c_2, \dots, c_n\}$, where each $c_i$ represents an academic course.
* **Edge Set $E$:** An edge $(u, v) \in E$ exists if and only if there exists at least one student $s \in S$ enrolled in both course $u$ and course $v$:
  $$E = \{(u, v) \in V \times V \mid u \neq v \land \text{Enrollment}(u) \cap \text{Enrollment}(v) \neq \emptyset\}$$
* **Edge Weight $w(u, v)$:** The number of mutual students:
  $$w(u, v) = |\text{Enrollment}(u) \cap \text{Enrollment}(v)|$$

### 2.2 Hard Constraints (Invariants)
1. **Conflict-Free Invariant:** No student shall be scheduled for two exams simultaneously:
   $$\forall (u, v) \in E \implies \text{Slot}(u) \neq \text{Slot}(v)$$
2. **Completeness Invariant:** Every course $c \in V$ must be scheduled in exactly one slot:
   $$\forall c \in V, \quad |\text{Slot}(c)| = 1, \quad \text{Slot}(c) \in \{0, 1, \dots, k-1\}$$
3. **Room Capacity & Non-Overlap:** For every slot $t$, the total seating capacity allocated to course $c$ must be $\ge |\text{Enrollment}(c)|$, and no room $r$ can be assigned to multiple courses in the same slot $t$.

### 2.3 Soft Constraints & Objective Function
Minimize the weighted multi-objective cost:
$$\min \mathcal{Z} = \alpha \cdot k + \beta \sum_{s \in S} \text{FatiguePenalty}(s) + \gamma \cdot \text{Var}(\text{SlotHeadcount})$$
where:
* $k$ is the total number of distinct time slots used ($\chi(G)$).
* $\text{FatiguePenalty}(s)$ penalizes consecutive exams ($|t_1 - t_2| = 1$) and multi-exam days.
* $\text{Var}(\text{SlotHeadcount})$ ensures balanced invigilator workload.

---

## 3. Algorithmic Design & Theoretical Foundations

```
+--------------------------------------------------------------------------------+
|                          STUDENT ENROLLMENT DATA                               |
+--------------------------------------------------------------------------------+
                                       |
                                       v
+--------------------------------------------------------------------------------+
|                   1. CONFLICT GRAPH BUILDER G = (V, E)                         |
|   - Compute degrees d(v), density D, and Maximal Clique Lower Bound omega(G)   |
+--------------------------------------------------------------------------------+
                                       |
                                       v
+--------------------------------------------------------------------------------+
|                   2. UPPER BOUND HEURISTICS (Welsh-Powell / DSatur)            |
|   - Fast greedy coloring establishing upper bound U = chi_greedy               |
+--------------------------------------------------------------------------------+
                                       |
                                       v
+--------------------------------------------------------------------------------+
|                   3. BRANCH & BOUND / EXACT CSP BACKTRACKING                   |
|   - Pre-color max clique omega(G) (Symmetry Breaking)                          |
|   - Forward checking + MRV variable selection                                  |
|   - Prune any sub-tree where k >= current best upper bound U                   |
+--------------------------------------------------------------------------------+
                                       |
                                       v
+--------------------------------------------------------------------------------+
|                   4. SOFT CONSTRAINT PERMUTATION OPTIMIZER                     |
|   - 2-Opt / Exact Permutation Search to minimize consecutive student fatigue   |
+--------------------------------------------------------------------------------+
                                       |
                                       v
+--------------------------------------------------------------------------------+
|                   5. ROOM ALLOCATION (Best-Fit Decreasing)                     |
|   - Multi-capacity bin packing for examination venues                          |
+--------------------------------------------------------------------------------+
                                       |
                                       v
+--------------------------------------------------------------------------------+
|                   6. FORMAL INVARIANT VERIFICATION AUDIT                       |
|   - 100% zero-clash verification across all students & rooms                   |
+--------------------------------------------------------------------------------+
```

### 3.1 Greedy Heuristics
1. **Welsh-Powell (Largest-Degree-First):**
   - Orders vertices by degree descending: $\deg(v_1) \ge \deg(v_2) \ge \dots \ge \deg(v_n)$.
   - Greedily assigns the lowest conflict-free color.
   - **Time Complexity:** $O(|V| \log |V| + |V|^2)$.
2. **DSatur (Degree of Saturation - Brélaz):**
   - Dynamically selects the uncolored vertex with the highest **saturation degree** (number of distinct colors assigned to its neighbors).
   - Breaks ties using uncolored degree.
   - **Time Complexity:** $O(|V|^2)$.

### 3.2 Exact CSP Backtracking Engine
- **MRV (Minimum Remaining Values):** Chooses $v \in V$ with $|D(v)|$ minimal to trigger early failures.
- **Degree Heuristic:** Breaks MRV ties by prioritizing vertices with the most unassigned neighbors.
- **Forward Checking (FC):** Prunes assigned color from neighbors' domains; backtracks immediately if any domain $|D(u)| = 0$.

### 3.3 Branch and Bound Strategy
- **Lower Bound ($L$):** Computed via greedy maximal clique $\omega(G) \le \chi(G)$.
- **Upper Bound ($U$):** Initialized with $\min(\chi_{\text{DSatur}}, \chi_{\text{WP}})$.
- **Symmetry Breaking:** Pre-colors the maximal clique $K_{\omega}$ with colors $\{0, 1, \dots, \omega-1\}$. Vertices outside the clique can only pick used colors or at most one new color $\max(\text{used}) + 1$.
- **Pruning Rule:** Prune subtree if $\text{colors\_used} \ge U$.

---

## 4. Asymptotic Complexity Analysis

| Component / Algorithm | Best-Case Time | Average-Case Time | Worst-Case Time | Space Complexity |
|---|---|---|---|---|
| **Conflict Graph Construction** | $\Omega(\|S\| \cdot k^2)$ | $\Theta(\|S\| \cdot k^2)$ | $O(\|S\| \cdot k^2)$ | $O(\|V\| + \|E\|)$ |
| **Max Clique Heuristic ($\omega(G)$)** | $\Omega(\|V\|)$ | $\Theta(\|V\|^2)$ | $O(\|V\|^2)$ | $O(\|V\|)$ |
| **Welsh-Powell Algorithm** | $\Omega(\|V\| \log \|V\|)$ | $\Theta(\|V\|^2)$ | $O(\|V\|^2 + \|E\|)$ | $O(\|V\|)$ |
| **DSatur Algorithm** | $\Omega(\|V\|^2)$ | $\Theta(\|V\|^2)$ | $O(\|V\|^2)$ | $O(\|V\| + \|E\|)$ |
| **Naive Backtracking** | $\Omega(\|V\|)$ | $\Theta(k^{\|V\|})$ | $O(k^{\|V\|})$ | $O(\|V\|)$ |
| **CSP Backtracking (MRV + FC)** | $\Omega(\|V\|)$ | Exponential (Heavily Pruned) | $O(k^{\|V\|})$ | $O(\|V\| \cdot k)$ |
| **Branch and Bound ($\chi(G)$)** | $\Omega(\|V\|^2)$ (when $\omega = U$) | Sub-exponential | $O(k^{\|V\|})$ | $O(\|V\| \cdot k)$ |
| **Best-Fit Room Allocation** | $\Omega(\|V_t\| \log \|R\|)$ | $\Theta(\|V_t\| \log \|R\|)$ | $O(\|V_t\| \cdot \|R\|)$ | $O(\|R\|)$ |

*Note: $\|V\| = \text{number of courses}$, $\|E\| = \text{conflict edges}$, $\|S\| = \text{number of students}$, $k = \text{time slots}$, $\|R\| = \text{rooms}$.*

---

## 5. Project Directory Structure

```
DAA PROJECT/
│
├── models.py                     # Data models (Course, Student, Room, TimeSlot, ScheduleResult)
├── graph_builder.py              # Conflict Graph, Degree metrics, Clique Lower Bound ω(G)
│
├── algorithms/
│   ├── __init__.py
│   ├── greedy_heuristics.py      # Welsh-Powell & DSatur greedy graph coloring
│   ├── exact_backtracking.py     # Backtracking CSP with MRV, Degree Heuristic & Forward Checking
│   ├── branch_and_bound.py       # Branch and Bound exact chromatic optimization
│   └── scheduler_engine.py       # End-to-end pipeline (Coloring + Soft-opt + Room packing)
│
├── validator.py                  # Formal zero-clash & capacity invariant auditor
├── sample_data.py                # Academic university dataset & synthetic benchmark generator
├── benchmark.py                  # Empirical performance & asymptotic scaling suite
├── main.py                       # CLI execution entry point & timetable visualizer
├── app.py                        # Interactive Streamlit Web Application Frontend
├── requirements.txt              # Python dependencies
└── README.md                     # Comprehensive academic documentation
```

---

## 6. How to Run and Reproduce

### 6.1 Run the Interactive Streamlit Web Application
Launches the interactive web dashboard with graph visualization, CSV upload/export, multi-algorithm comparisons, and personalized student schedules:
```bash
streamlit run "C:\Users\ADMIN\OneDrive\Desktop\cloude\DAA PROJECT\app.py"
```

### 6.2 Run the Full Scheduling Demonstration (CLI)
Executes graph building, algorithmic comparison, optimal timetable generation, and formal invariant validation:
```bash
python "C:\Users\ADMIN\OneDrive\Desktop\cloude\DAA PROJECT\main.py"
```

### 6.2 Run the Empirical Asymptotic Scaling Benchmark
Runs scaling experiments across synthetic graphs from $|V|=10$ to $|V|=60$ measuring runtimes and pruned search nodes:
```bash
python "C:\Users\ADMIN\OneDrive\Desktop\cloude\DAA PROJECT\benchmark.py"
```

---

## 7. Sample Execution Output

```
================================================================================
   INTELLIGENT EXAM SCHEDULING SYSTEM (DAA CAPSTONE PROJECT)
   Graph Colouring, Exact Backtracking & Branch and Bound Optimization
================================================================================

[1] DATASET INITIALIZED:
    - Total Courses (|V|) : 12
    - Total Students (|S|): 190
    - Available Exam Rooms : 8

[2] CONFLICT GRAPH ANALYSIS (G = (V, E)):
    - Total Vertices (|V|)   : 12
    - Total Conflict Edges (|E|): 57
    - Graph Density (D)       : 0.8636 (Dense/Interconnected)
    - Max Degree Δ(G)         : 11 (Course: MA301)
    - Min Degree δ(G)         : 8 (Course: AI303)
    - Lower Bound ω(G) [Clique]: 8 slots (Theoretical Minimum)
    - Maximal Clique Sample   : ['IT301', 'MA301', 'CS304', 'CS302', 'AI302', 'CS301', 'DS301', 'CS303']

[3] ALGORITHMIC COMPARISON ON CONFLICT GRAPH:
Algorithm        | Total Slots (k) | Time (ms) | Student Clashes | Consecutive Penalty | Valid?           
-----------------+-----------------+-----------+-----------------+---------------------+------------------
Welsh Powell     | 8               | 49.98     | 0               | 521                 | PASS [Zero Clash]
Dsatur           | 8               | 48.90     | 0               | 521                 | PASS [Zero Clash]
Backtracking     | 8               | 49.14     | 0               | 521                 | PASS [Zero Clash]
Branch And Bound | 8               | 52.35     | 0               | 521                 | PASS [Zero Clash]

[4] OPTIMAL EXAM TIMETABLE (Generated via BRANCH_AND_BOUND):
    * Slots per day: 2 (Morning: 09:00 - 12:00 | Afternoon: 14:00 - 17:00)

Slot ID | Day   | Session                   | Course Code | Course Title                                    | Students | Allocated Rooms
--------+-------+---------------------------+-------------+-------------------------------------------------+----------+----------------
Slot #1 | Day 1 | Morning (09:00 - 12:00)   | IT301       | Computer Networks & Distributed Systems         | 100      | LH_MEGHA_101   
        |       |                           | DS302       | Applied Statistics & Stochastic Modeling        | 80       | LH_ARYAB_201   
Slot #2 | Day 1 | Afternoon (14:00 - 17:00) | CS302       | Operating Systems & Systems Programming         | 105      | LH_MEGHA_101   
        |       |                           | AI303       | Deep Learning & Neural Architectures            | 32       | LAB_LOVELACE_AI
Slot #3 | Day 2 | Morning (09:00 - 12:00)   | CS303       | Database Management Systems & SQL               | 112      | LH_MEGHA_101   
Slot #4 | Day 2 | Afternoon (14:00 - 17:00) | AI302       | Machine Learning & Pattern Recognition          | 85       | LH_ARYAB_201   
        |       |                           | EC301       | Microprocessors & Embedded Systems              | 35       | LAB_LOVELACE_AI
Slot #5 | Day 3 | Morning (09:00 - 12:00)   | CS304       | Software Engineering & Cloud Architecture       | 80       | LH_ARYAB_201   
Slot #6 | Day 3 | Afternoon (14:00 - 17:00) | CS301       | Data Structures & Algorithms                    | 160      | HALL_CONVOC    
Slot #7 | Day 4 | Morning (09:00 - 12:00)   | DS301       | Big Data Analytics & Data Mining                | 61       | LH_BHASK_301   
        |       |                           | AI301       | Artificial Intelligence & Expert Systems        | 60       | LAB_TURING_CS  
Slot #8 | Day 4 | Afternoon (14:00 - 17:00) | MA301       | Discrete Mathematical Structures & Graph Theory | 175      | HALL_CONVOC    

[5] FORMAL CONSTRAINT VALIDATION AUDIT:
    - is_valid                      : True
    - total_courses_audited         : 12
    - total_students_audited        : 190
    - total_slots_used              : 8
    - graph_edge_violations         : 0
    - student_clashes               : 0
    - room_double_bookings          : 0
    - room_capacity_shortages       : 0
    - status                        : PASSED (Conflict-Free)

[+] SUCCESS: Verified 100% Conflict-Free Schedule across all 190 students and 12 courses!
```
