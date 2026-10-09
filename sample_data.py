"""
sample_data.py
--------------
Generates realistic academic university datasets, authentic exam cell records,
and synthetic benchmark instances.

Includes:
1. Authentic 12 Core & Elective Engineering courses across multiple departments
   (CSE, AIML, CSDS, IT, ECE, MATH) with realistic department codes and credit weights.
2. Comprehensive student population of 190 students across 6 distinct academic branches
   with realistic registration numbers, student names, and overlapping elective enrollments.
3. 8 Examination venues comprising Central Auditoriums, Convocational Halls,
   Mega Lecture Theatres, and High-Performance Computer Labs (capacities 50 to 250).
4. CSV Exporter and Importer utilities for courses.csv, students.csv, and rooms.csv.
"""

import os
import csv
import random
from typing import List, Tuple, Set, Optional
from models import Course, Student, Room


# ---------------- Authentic University Examination Records ----------------

RAW_COURSES = [
    {
        "id": "CS301",
        "code": "CS301",
        "name": "Data Structures & Algorithms",
        "department": "Computer Science & Engineering",
        "credits": 4,
    },
    {
        "id": "CS302",
        "code": "CS302",
        "name": "Operating Systems & Systems Programming",
        "department": "Computer Science & Engineering",
        "credits": 4,
    },
    {
        "id": "CS303",
        "code": "CS303",
        "name": "Database Management Systems & SQL",
        "department": "Computer Science & Engineering",
        "credits": 3,
    },
    {
        "id": "CS304",
        "code": "CS304",
        "name": "Software Engineering & Cloud Architecture",
        "department": "Computer Science & Engineering",
        "credits": 3,
    },
    {
        "id": "AI301",
        "code": "AI301",
        "name": "Artificial Intelligence & Expert Systems",
        "department": "AI & Machine Learning",
        "credits": 4,
    },
    {
        "id": "AI302",
        "code": "AI302",
        "name": "Machine Learning & Pattern Recognition",
        "department": "AI & Machine Learning",
        "credits": 4,
    },
    {
        "id": "AI303",
        "code": "AI303",
        "name": "Deep Learning & Neural Architectures",
        "department": "AI & Machine Learning",
        "credits": 3,
    },
    {
        "id": "DS301",
        "code": "DS301",
        "name": "Big Data Analytics & Data Mining",
        "department": "Data Science & Analytics",
        "credits": 3,
    },
    {
        "id": "DS302",
        "code": "DS302",
        "name": "Applied Statistics & Stochastic Modeling",
        "department": "Data Science & Analytics",
        "credits": 3,
    },
    {
        "id": "IT301",
        "code": "IT301",
        "name": "Computer Networks & Distributed Systems",
        "department": "Information Technology",
        "credits": 4,
    },
    {
        "id": "EC301",
        "code": "EC301",
        "name": "Microprocessors & Embedded Systems",
        "department": "Electronics & Communication",
        "credits": 4,
    },
    {
        "id": "MA301",
        "code": "MA301",
        "name": "Discrete Mathematical Structures & Graph Theory",
        "department": "Mathematics & Computing",
        "credits": 4,
    },
]

RAW_ROOMS = [
    {
        "id": "AUD_CENTRAL",
        "name": "Dr. APJ Abdul Kalam Central Auditorium",
        "capacity": 250,
        "building": "Convention Centre",
        "room_type": "Central Auditorium",
    },
    {
        "id": "HALL_CONVOC",
        "name": "Sir C.V. Raman Convocational Exam Hall",
        "capacity": 180,
        "building": "Academic Block A",
        "room_type": "Main Examination Hall",
    },
    {
        "id": "LH_MEGHA_101",
        "name": "Meghnad Saha Mega Lecture Theatre 101",
        "capacity": 120,
        "building": "Science Complex",
        "room_type": "Tiered Lecture Theatre",
    },
    {
        "id": "LH_ARYAB_201",
        "name": "Aryabhata Lecture Hall 201",
        "capacity": 90,
        "building": "Engineering Block B",
        "room_type": "Standard Exam Hall",
    },
    {
        "id": "LH_BHASK_301",
        "name": "Bhaskara Lecture Hall 301",
        "capacity": 75,
        "building": "Engineering Block B",
        "room_type": "Standard Exam Hall",
    },
    {
        "id": "LAB_TURING_CS",
        "name": "Alan Turing High-Performance Computing Lab",
        "capacity": 60,
        "building": "CS & AI Complex",
        "room_type": "Computer Examination Lab",
    },
    {
        "id": "LAB_LOVELACE_AI",
        "name": "Ada Lovelace AI & Data Science Lab",
        "capacity": 50,
        "building": "CS & AI Complex",
        "room_type": "Computer Examination Lab",
    },
    {
        "id": "SEMINAR_VISVES_401",
        "name": "Sir M. Visvesvaraya Seminar Complex 401",
        "capacity": 50,
        "building": "Admin & Exam Block",
        "room_type": "Exam Seminar Hall",
    },
]

# Authentic University Student Cohort Registry (190 Students across 6 Branches)
COHORT_STUDENT_NAMES = [
    # CSE Cohort (45 students)
    "Aarav Sharma", "Aditi Patel", "Rohan Gupta", "Ananya Iyer", "Aryan Singh",
    "Diya Nair", "Vihaan Reddy", "Ishita Sen", "Kabir Mukherjee", "Riya Joshi",
    "Dev Malhotra", "Tanvi Deshmukh", "Reyansh Rao", "Meera Kulkarni", "Shaurya Verma",
    "Pooja Menon", "Siddharth Jain", "Sneha Nambiar", "Atharv Bhat", "Avani Saxena",
    "Pranav Chawla", "Khushi Agarwal", "Dhruv Hegde", "Kriti Trivedi", "Harsh Vardhan",
    "Rashi Kapoor", "Aditya Pillai", "Samaira Bose", "Arjun Dasgupta", "Nisha Choudhury",
    "Yash Singhania", "Bhavna Mehra", "Manan Goyal", "Lavanya Venkatesh", "Varun Kaushik",
    "Simran Sandhu", "Rishabh Tiwari", "Disha Pandey", "Tanishq Sethi", "Saumya Mishra",
    "Nikhil Dutta", "Neha Grover", "Kunal Rastogi", "Palak Ahuja", "Ayush Bhattacharya",

    # AIML Cohort (40 students)
    "Aniruddh Prasad", "Shreya Banerjee", "Vedant Kulkarni", "Radhika Mittal", "Parthiv Shah",
    "Akanksha Goswami", "Harshit Rawat", "Swati Mahajan", "Samarth Soni", "Anwesha Chakraborty",
    "Tejas Marathe", "Garima Mathur", "Ojas Patil", "Ishani Ghosh", "Chirag Somani",
    "Muskan Singhal", "Abhay Bhardwaj", "Niharika Saraf", "Samarjit Roy", "Pragya Dwivedi",
    "Keshav Bajaj", "Vrinda Chopra", "Arnav Jindal", "Mahi Kashyap", "Gaurav Saran",
    "Hansika Khatri", "Tanmay Vashisht", "Sonali Pradhan", "Utkarsh Srivastava", "Navya Sundaram",
    "Karthik Natarajan", "Pavithra Sundar", "Prateek Oberoi", "Divya Suri", "Aayush Lodha",
    "Shambhavi Shukla", "Devansh Kaul", "Jagruti Lal", "Mayank Dogra", "Charu Anand",

    # CSDS Cohort (35 students)
    "Darshil Modi", "Sanjana Gokhale", "Eeshan Tambe", "Vidhi Somani", "Neil Barua",
    "Ruchika Sen", "Alok Ranjan", "Trisha Poddar", "Hardik Tandon", "Mallika Sheth",
    "Raghavendra Shenoy", "Priyanka Kurup", "Sarthak Ganguly", "Jhanvi Morparia", "Kshitij Puranik",
    "Shraddha Salunkhe", "Vansh Batra", "Ananya Majumdar", "Kushal Chhabra", "Srishti Talwar",
    "Jayesh Wadhwa", "Shweta Nayak", "Mihir Merchant", "Tanuja Dube", "Amartya Sen",
    "Nandini Parekh", "Chinmay Khare", "Urvashi Rathi", "Sahil Duggal", "Richa Sengupta",
    "Deepak Narang", "Avantika Som", "Sourabh Birje", "Anamika Das", "Karan Joharilal",

    # IT Cohort (30 students)
    "Chetna Rawal", "Mohit Grewal", "Saloni Khurana", "Bharat Bhushan", "Ipsita Panda",
    "Sujay Mukhopadhyay", "Tanya Chadha", "Rahul Nanda", "Shweta Biswas", "Rohitashva Pant",
    "Shruti Kothari", "Girish Vaidya", "Damini Bhasin", "Sandeep Grewal", "Archana Hegde",
    "Vikramaditya Sen", "Purnima Seth", "Abhinav Kaushik", "Leena Gangadharan", "Madhavan Nair",
    "Meenakshi Sundaram", "Jayant Prabhu", "Shalini Acharya", "Suresh Subramanian", "Padmaja Rangachari",
    "Hemant Kulkarni", "Vasudha Nadkarni", "Mukund Joshi", "Renuka Oak", "Raghavendra Pai",

    # ECE Cohort (25 students)
    "Suhasini Kamat", "Vivek Marathe", "Mridula Kulkarni", "Omkar Deshpande", "Ketaki Godbole",
    "Anil Deshmukh", "Sunita Shinde", "Dilip Mane", "Rekha Patil", "Pramod Jadhav",
    "Vandana Bhosale", "Chetan Gaikwad", "Sharmila Sawant", "Shrikant Salvi", "Aparna More",
    "Ravindra Kadam", "Rohini Koli", "Vijay Tawde", "Smita Pawar", "Milind Rane",
    "Manisha Sathe", "Nilesh Thorat", "Pallavi Ghodke", "Sanjay Kute", "Jyoti Landge",

    # Honors & Dual Degree Cohort (15 students)
    "Mahendra Dhage", "Aruna Garje", "Babasaheb Shinde", "Chhaya Solanke", "Govind Gore",
    "Sushila Rathod", "Santosh Chavan", "Jayshree Gavit", "Dnyaneshwar Valvi", "Latika Padvi",
    "Subhash Tadvi", "Sangeeta Vasave", "Prakash Naik", "Usha Velip", "Tukaram Gaonkar"
]


def get_academic_dataset() -> Tuple[List[Course], List[Student], List[Room]]:
    """
    Returns the authentic University Examination Dataset comprising 12 Engineering courses,
    190 students across 6 distinct academic branches, and 8 examination halls (50-250 seats).
    """
    # 1. Build Course Objects
    courses = [
        Course(
            id=c["id"],
            code=c["code"],
            name=c["name"],
            department=c["department"],
            credits=c["credits"],
        )
        for c in RAW_COURSES
    ]

    # 2. Build Room Objects
    rooms = [
        Room(
            id=r["id"],
            name=r["name"],
            capacity=r["capacity"],
            building=r["building"],
            room_type=r["room_type"],
        )
        for r in RAW_ROOMS
    ]

    # 3. Build Student Cohort Enrollments
    students: List[Student] = []
    name_idx = 0

    # --- Cohort 1: B.Tech CSE (45 students) ---
    # Core: CS301 (DSA), CS302 (OS), CS303 (DBMS), IT301 (Networks), MA301 (Discrete Math)
    # Elective: 25 take CS304 (Software Engg), 20 take AI302 (Machine Learning)
    for i in range(1, 46):
        s_id = f"2024BCSE{i:03d}"
        s_name = COHORT_STUDENT_NAMES[name_idx]
        name_idx += 1
        core_courses = {"CS301", "CS302", "CS303", "IT301", "MA301"}
        elective = {"CS304"} if i <= 25 else {"AI302"}
        enrolled = core_courses | elective
        students.append(Student(id=s_id, name=s_name, branch="Computer Science & Engineering", enrolled_courses=enrolled))

    # --- Cohort 2: B.Tech AIML (40 students) ---
    # Core: CS301 (DSA), AI301 (AI), AI302 (ML), DS302 (Applied Stats), MA301 (Discrete Math)
    # Elective: 22 take AI303 (Deep Learning), 18 take CS303 (DBMS)
    for i in range(1, 41):
        s_id = f"2024BAIML{i:03d}"
        s_name = COHORT_STUDENT_NAMES[name_idx]
        name_idx += 1
        core_courses = {"CS301", "AI301", "AI302", "DS302", "MA301"}
        elective = {"AI303"} if i <= 22 else {"CS303"}
        enrolled = core_courses | elective
        students.append(Student(id=s_id, name=s_name, branch="AI & Machine Learning", enrolled_courses=enrolled))

    # --- Cohort 3: B.Tech CSDS (35 students) ---
    # Core: CS301 (DSA), DS301 (Big Data), DS302 (Applied Stats), CS303 (DBMS), MA301 (Discrete Math)
    # Elective: 20 take AI302 (ML), 15 take CS304 (Software Engg)
    for i in range(1, 36):
        s_id = f"2024BCSDS{i:03d}"
        s_name = COHORT_STUDENT_NAMES[name_idx]
        name_idx += 1
        core_courses = {"CS301", "DS301", "DS302", "CS303", "MA301"}
        elective = {"AI302"} if i <= 20 else {"CS304"}
        enrolled = core_courses | elective
        students.append(Student(id=s_id, name=s_name, branch="Data Science & Analytics", enrolled_courses=enrolled))

    # --- Cohort 4: B.Tech IT (30 students) ---
    # Core: CS301 (DSA), CS302 (OS), IT301 (Networks), CS304 (Software Engg), MA301 (Discrete Math)
    # Elective: 16 take DS301 (Big Data), 14 take CS303 (DBMS)
    for i in range(1, 31):
        s_id = f"2024BIT{i:03d}"
        s_name = COHORT_STUDENT_NAMES[name_idx]
        name_idx += 1
        core_courses = {"CS301", "CS302", "IT301", "CS304", "MA301"}
        elective = {"DS301"} if i <= 16 else {"CS303"}
        enrolled = core_courses | elective
        students.append(Student(id=s_id, name=s_name, branch="Information Technology", enrolled_courses=enrolled))

    # --- Cohort 5: B.Tech ECE (25 students) ---
    # Core: EC301 (Microprocessors), IT301 (Networks), CS302 (OS), MA301 (Discrete Math)
    # Elective: 15 take AI301 (AI), 10 take CS301 (DSA)
    for i in range(1, 26):
        s_id = f"2024BECE{i:03d}"
        s_name = COHORT_STUDENT_NAMES[name_idx]
        name_idx += 1
        core_courses = {"EC301", "IT301", "CS302", "MA301"}
        elective = {"AI301"} if i <= 15 else {"CS301"}
        enrolled = core_courses | elective
        students.append(Student(id=s_id, name=s_name, branch="Electronics & Communication", enrolled_courses=enrolled))

    # --- Cohort 6: Honors & Dual Degree Program (15 students) ---
    # Interdisciplinary & Advanced Elective combinations
    for i in range(1, 16):
        s_id = f"2023BHON{i:03d}"
        s_name = COHORT_STUDENT_NAMES[name_idx]
        name_idx += 1
        if i <= 5:
            enrolled = {"AI303", "DS301", "EC301", "CS304"}
        elif i <= 10:
            enrolled = {"AI301", "AI303", "DS302", "EC301"}
        else:
            enrolled = {"CS302", "DS301", "AI302", "CS304"}
        students.append(Student(id=s_id, name=s_name, branch="Honors & Dual Degree", enrolled_courses=enrolled))

    # Register enrolled students into Course objects
    course_map = {c.id: c for c in courses}
    for stu in students:
        for cid in stu.enrolled_courses:
            if cid in course_map:
                course_map[cid].enrolled_students.add(stu.id)

    return courses, students, rooms


DEFAULT_DATA_DIR = os.path.dirname(os.path.abspath(__file__))


def export_dataset_to_csv(
    courses: Optional[List[Course]] = None,
    students: Optional[List[Student]] = None,
    rooms: Optional[List[Room]] = None,
    output_dir: Optional[str] = None,
) -> Tuple[str, str, str]:
    """
    Exports courses, students, and rooms to standard CSV files inside output_dir
    (defaults to the DAA PROJECT folder).
    Returns the file paths: (courses_path, students_path, rooms_path).
    """
    if output_dir is None:
        output_dir = DEFAULT_DATA_DIR

    if courses is None or students is None or rooms is None:
        courses, students, rooms = get_academic_dataset()

    os.makedirs(output_dir, exist_ok=True)
    courses_path = os.path.join(output_dir, "courses.csv")
    students_path = os.path.join(output_dir, "students.csv")
    rooms_path = os.path.join(output_dir, "rooms.csv")

    # 1. Write courses.csv
    with open(courses_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "code", "name", "department", "credits"])
        for c in courses:
            writer.writerow([c.id, c.code, c.name, getattr(c, "department", "Engineering"), getattr(c, "credits", 4)])

    # 2. Write students.csv
    with open(students_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "branch", "enrolled_courses"])
        for s in students:
            courses_str = ";".join(sorted(s.enrolled_courses))
            writer.writerow([s.id, s.name, getattr(s, "branch", "General"), courses_str])

    # 3. Write rooms.csv
    with open(rooms_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "capacity", "building", "room_type"])
        for r in rooms:
            writer.writerow([r.id, r.name, r.capacity, r.building, getattr(r, "room_type", "Exam Hall")])

    return courses_path, students_path, rooms_path


def load_dataset_from_csv(
    csv_dir: Optional[str] = None,
) -> Tuple[List[Course], List[Student], List[Room]]:
    """
    Loads courses, students, and rooms from CSV files inside csv_dir
    (defaults to the DAA PROJECT folder).
    If CSV files are missing, generates and exports default dataset first.
    """
    if csv_dir is None:
        csv_dir = DEFAULT_DATA_DIR

    courses_path = os.path.join(csv_dir, "courses.csv")
    students_path = os.path.join(csv_dir, "students.csv")
    rooms_path = os.path.join(csv_dir, "rooms.csv")

    if not (os.path.exists(courses_path) and os.path.exists(students_path) and os.path.exists(rooms_path)):
        export_dataset_to_csv(output_dir=csv_dir)

    courses: List[Course] = []
    with open(courses_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            courses.append(
                Course(
                    id=row["id"].strip(),
                    code=row.get("code", row["id"]).strip(),
                    name=row.get("name", row["id"]).strip(),
                    department=row.get("department", "Engineering").strip(),
                    credits=int(row.get("credits", 4)),
                )
            )

    rooms: List[Room] = []
    with open(rooms_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rooms.append(
                Room(
                    id=row["id"].strip(),
                    name=row.get("name", row["id"]).strip(),
                    capacity=int(row["capacity"]),
                    building=row.get("building", "Main Block").strip(),
                    room_type=row.get("room_type", "Exam Hall").strip(),
                )
            )

    students: List[Student] = []
    course_map = {c.id: c for c in courses}
    with open(students_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            s_id = row["id"].strip()
            s_name = row.get("name", s_id).strip()
            branch = row.get("branch", "General").strip()
            raw_enrolled = row["enrolled_courses"].split(";")
            enrolled = {c.strip() for c in raw_enrolled if c.strip()}
            s_obj = Student(id=s_id, name=s_name, branch=branch, enrolled_courses=enrolled)
            students.append(s_obj)

            for cid in enrolled:
                if cid in course_map:
                    course_map[cid].enrolled_students.add(s_id)

    return courses, students, rooms


def generate_synthetic_dataset(
    num_courses: int = 30,
    num_students: int = 200,
    courses_per_student: int = 4,
    seed: int = 42,
) -> Tuple[List[Course], List[Student], List[Room]]:
    """
    Generates synthetic benchmark graphs with controllable density and size
    for asymptotic complexity experiments.
    """
    random.seed(seed)

    departments = ["Computer Science", "AI & Data Science", "Information Technology", "Electronics"]
    courses = [
        Course(
            id=f"CRS_{i:03d}",
            code=f"C{i:03d}",
            name=f"Academic Course {i}",
            department=departments[i % len(departments)],
            credits=3 + (i % 2),
        )
        for i in range(num_courses)
    ]

    students: List[Student] = []
    for s_idx in range(num_students):
        s_id = f"SYN_STU_{s_idx:04d}"
        enrolled_courses = set(
            random.sample([c.id for c in courses], min(courses_per_student, num_courses))
        )
        students.append(
            Student(
                id=s_id,
                name=f"Synthetic Student {s_idx + 1}",
                branch="Synthetic Engineering",
                enrolled_courses=enrolled_courses,
            )
        )

    rooms = [
        Room(
            id=f"ROOM_{r}",
            name=f"Exam Hall {r}",
            capacity=random.randint(50, 200),
            building="North Campus",
            room_type="Exam Hall",
        )
        for r in range(max(4, num_courses // 3))
    ]

    return courses, students, rooms


if __name__ == "__main__":
    c_p, s_p, r_p = export_dataset_to_csv()
    print(f"Generated CSVs successfully inside DAA PROJECT:\n - {c_p}\n - {s_p}\n - {r_p}")
