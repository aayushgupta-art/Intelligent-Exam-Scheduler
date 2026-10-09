"""
sample_data.py
--------------
Generates realistic academic university datasets for enterprise exam scheduling.

Includes:
1. 15-18 Core & Elective Engineering courses across 4 academic years
2. 250+ students with institutional PRNs (2024BCSE001, 2025BIT045) across all years
   - First Year (Sem 1-2), Second Year (Sem 3-4), Third Year (Sem 5-6), Final Year (Sem 7-8)
   - Branch classifications: CSE, AIML, Data Science, IT, ECE
3. Examination venues with realistic capacities (30 to 300 seats)
4. CSV Export/Import utilities
"""

import os
import csv
import random
from typing import List, Tuple, Set, Optional
from models import Course, Student, Room

DEFAULT_DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------- Phase 1: Extended Course Catalog (18 Courses) ----------------

RAW_COURSES = [
    # First Year (Semester 1-2) - Foundation Courses
    {
        "id": "FY101", "code": "FY101", "name": "Engineering Mathematics I",
        "department": "First Year Engineering", "credits": 4,
        "academic_year": "First Year", "semester": "Semester 1",
        "paper_code": "P-COMMON-MATH1", "year_int": 1,
    },
    {
        "id": "FY102", "code": "FY102", "name": "Engineering Physics I",
        "department": "First Year Engineering", "credits": 3,
        "academic_year": "First Year", "semester": "Semester 1",
        "paper_code": "P-COMMON-PHYS1", "year_int": 1,
    },
    {
        "id": "FY103", "code": "FY103", "name": "Programming Fundamentals & C",
        "department": "First Year Engineering", "credits": 4,
        "academic_year": "First Year", "semester": "Semester 2",
        "paper_code": "P-COMMON-PROG", "year_int": 1,
    },
    # Second Year (Semester 3-4) - Core Building Blocks
    {
        "id": "SY201", "code": "SY201", "name": "Data Structures & Algorithms",
        "department": "Computer Science & Engineering", "credits": 4,
        "academic_year": "Second Year", "semester": "Semester 3",
        "paper_code": "P-CSE201-DSA", "year_int": 2,
    },
    {
        "id": "SY202", "code": "SY202", "name": "Discrete Mathematics",
        "department": "Mathematics & Computing", "credits": 3,
        "academic_year": "Second Year", "semester": "Semester 3",
        "paper_code": "P-COMMON-DISCMATH", "year_int": 2,
    },
    {
        "id": "SY203", "code": "SY203", "name": "Digital Logic Design",
        "department": "Electronics & Communication", "credits": 4,
        "academic_year": "Second Year", "semester": "Semester 4",
        "paper_code": "P-ECE203-DLD", "year_int": 2,
    },
    # Third Year (Semester 5-6) - Advanced Core & Electives
    {
        "id": "TY301", "code": "TY301", "name": "Operating Systems & Systems Programming",
        "department": "Computer Science & Engineering", "credits": 4,
        "academic_year": "Third Year", "semester": "Semester 5",
        "paper_code": "P-CSE301-OS", "year_int": 3,
    },
    {
        "id": "TY302", "code": "TY302", "name": "Database Management Systems",
        "department": "Computer Science & Engineering", "credits": 3,
        "academic_year": "Third Year", "semester": "Semester 5",
        "paper_code": "P-CSE302-DBMS", "year_int": 3,
    },
    {
        "id": "TY303", "code": "TY303", "name": "Artificial Intelligence & Expert Systems",
        "department": "AI & Machine Learning", "credits": 4,
        "academic_year": "Third Year", "semester": "Semester 5",
        "paper_code": "P-AIML301-AI", "year_int": 3,
    },
    {
        "id": "TY304", "code": "TY304", "name": "Machine Learning Fundamentals",
        "department": "AI & Machine Learning", "credits": 4,
        "academic_year": "Third Year", "semester": "Semester 6",
        "paper_code": "P-AIML302-ML", "year_int": 3,
    },
    {
        "id": "TY305", "code": "TY305", "name": "Big Data Analytics & Mining",
        "department": "Data Science & Analytics", "credits": 3,
        "academic_year": "Third Year", "semester": "Semester 6",
        "paper_code": "P-DS301-BigData", "year_int": 3,
    },
    {
        "id": "TY306", "code": "TY306", "name": "Computer Networks & Distributed Systems",
        "department": "Information Technology", "credits": 4,
        "academic_year": "Third Year", "semester": "Semester 5",
        "paper_code": "P-IT301-CN", "year_int": 3,
    },
    # Final Year (Semester 7-8) - Specialized & Project
    {
        "id": "FY401", "code": "FY401", "name": "Deep Learning & Neural Architectures",
        "department": "AI & Machine Learning", "credits": 4,
        "academic_year": "Final Year", "semester": "Semester 7",
        "paper_code": "P-AIML401-DL", "year_int": 4,
    },
    {
        "id": "FY402", "code": "FY402", "name": "Software Engineering & Cloud Architecture",
        "department": "Computer Science & Engineering", "credits": 3,
        "academic_year": "Final Year", "semester": "Semester 7",
        "paper_code": "P-CSE401-SE", "year_int": 4,
    },
    {
        "id": "FY403", "code": "FY403", "name": "Cyber Security & Cryptography",
        "department": "Computer Science & Engineering", "credits": 4,
        "academic_year": "Final Year", "semester": "Semester 8",
        "paper_code": "P-CSE402-CYBER", "year_int": 4,
    },
    {
        "id": "FY404", "code": "FY404", "name": "Internet of Things & Embedded Systems",
        "department": "Electronics & Communication", "credits": 3,
        "academic_year": "Final Year", "semester": "Semester 8",
        "paper_code": "P-ECE401-IOT", "year_int": 4,
    },
    {
        "id": "FY405", "code": "FY405", "name": "Cloud Computing & DevOps",
        "department": "Information Technology", "credits": 3,
        "academic_year": "Final Year", "semester": "Semester 7",
        "paper_code": "P-IT401-CLOUD", "year_int": 4,
    },
    {
        "id": "FY406", "code": "FY406", "name": "Applied Statistics & Stochastic Modeling",
        "department": "Data Science & Analytics", "credits": 3,
        "academic_year": "Final Year", "semester": "Semester 7",
        "paper_code": "P-DS401-Stats", "year_int": 4,
    },
]

# ---------------- Phase 1: Examination Rooms (Diverse Capacities 30-300) ----------------

RAW_ROOMS = [
    {"id": "AUDIT_01", "name": "Dr. APJ Abdul Kalam Central Auditorium", "capacity": 300, "building": "Convention Centre", "room_type": "Central Auditorium"},
    {"id": "HALL_A", "name": "Mahatma Gandhi Convocational Hall", "capacity": 250, "building": "Academic Block A", "room_type": "Main Examination Hall"},
    {"id": "HALL_B", "name": "Sir C.V. Raman Examination Hall", "capacity": 200, "building": "Academic Block B", "room_type": "Main Examination Hall"},
    {"id": "LT_101", "name": "Aryabhata Lecture Theatre 101", "capacity": 120, "building": "Science Complex", "room_type": "Tiered Lecture Theatre"},
    {"id": "LT_102", "name": "Brahmagupta Lecture Theatre 102", "capacity": 100, "building": "Science Complex", "room_type": "Tiered Lecture Theatre"},
    {"id": "LH_201", "name": "Ramanujan Lecture Hall 201", "capacity": 80, "building": "Engineering Block A", "room_type": "Standard Exam Hall"},
    {"id": "LH_202", "name": "Hypatia Lecture Hall 202", "capacity": 75, "building": "Engineering Block A", "room_type": "Standard Exam Hall"},
    {"id": "LH_301", "name": "Noether Lecture Hall 301", "capacity": 60, "building": "Engineering Block B", "room_type": "Standard Exam Hall"},
    {"id": "LAB_CS1", "name": "Alan Turing High-Performance Computing Lab", "capacity": 50, "building": "CS & AI Complex", "room_type": "Computer Examination Lab"},
    {"id": "LAB_CS2", "name": "Ada Lovelace AI & Data Science Lab", "capacity": 45, "building": "CS & AI Complex", "room_type": "Computer Examination Lab"},
    {"id": "LAB_IT1", "name": "Grace Hopper Software Development Lab", "capacity": 40, "building": "IT Block", "room_type": "Computer Examination Lab"},
    {"id": "SEM_401", "name": "Visvesvaraya Seminar Complex 401", "capacity": 30, "building": "Admin & Exam Block", "room_type": "Exam Seminar Hall"},
]

# ---------------- Phase 1: Student Names Pool (250+) ----------------

STUDENT_NAME_POOL = [
    # CSE Branch
    "Aarav Sharma", "Aditi Patel", "Rohan Gupta", "Ananya Iyer", "Aryan Singh", "Diya Nair", "Vihaan Reddy",
    "Ishita Sen", "Kabir Mukherjee", "Riya Joshi", "Dev Malhotra", "Tanvi Deshmukh", "Reyansh Rao", "Meera Kulkarni",
    "Shaurya Verma", "Pooja Menon", "Siddharth Jain", "Sneha Nambiar", "Atharv Bhat", "Avani Saxena", "Pranav Chawla",
    "Khushi Agarwal", "Dhruv Hegde", "Kriti Trivedi", "Harsh Vardhan", "Rashi Kapoor", "Aditya Pillai", "Samaira Bose",
    "Arjun Dasgupta", "Nisha Choudhury", "Yash Singhania", "Bhavna Mehra", "Manan Goyal", "Lavanya Venkatesh", "Varun Kaushik",
    # AIML Branch
    "Aniruddh Prasad", "Shreya Banerjee", "Vedant Kulkarni", "Radhika Mittal", "Parthiv Shah", "Akanksha Goswami",
    "Harshit Rawat", "Swati Mahajan", "Samarth Soni", "Anwesha Chakraborty", "Tejas Marathe", "Garima Mathur",
    "Ojas Patil", "Ishani Ghosh", "Chirag Somani", "Muskan Singhal", "Abhay Bhardwaj", "Niharika Saraf", "Samarjit Roy",
    "Pragya Dwivedi", "Keshav Bajaj", "Vrinda Chopra", "Arnav Jindal", "Mahi Kashyap", "Gaurav Saran", "Hansika Khatri",
    "Tanmay Vashisht", "Sonali Pradhan", "Utkarsh Srivastava", "Navya Sundaram", "Karthik Natarajan", "Pavithra Sundar",
    # Data Science Branch
    "Darshil Modi", "Sanjana Gokhale", "Eeshan Tambe", "Vidhi Somani", "Neil Barua", "Ruchika Sen", "Alok Ranjan",
    "Trisha Poddar", "Hardik Tandon", "Mallika Sheth", "Raghavendra Shenoy", "Priyanka Kurup", "Sarthak Ganguly",
    "Jhanvi Morparia", "Kshitij Puranik", "Shraddha Salunkhe", "Vansh Batra", "Ananya Majumdar", "Kushal Chhabra",
    "Srishti Talwar", "Jayesh Wadhwa", "Shweta Nayak", "Mihir Merchant", "Tanuja Dube", "Amartya Sen", "Nandini Parekh",
    # IT Branch
    "Chetna Rawal", "Mohit Grewal", "Saloni Khurana", "Bharat Bhushan", "Ipsita Panda", "Sujay Mukhopadhyay",
    "Tanya Chadha", "Rahul Nanda", "Shweta Biswas", "Rohitashva Pant", "Shruti Kothari", "Girish Vaidya",
    "Damini Bhasin", "Sandeep Grewal", "Archana Hegde", "Vikramaditya Sen", "Purnima Seth", "Abhinav Kaushik",
    "Leena Gangadharan", "Madhavan Nair", "Meenakshi Sundaram", "Jayant Prabhu", "Shalini Acharya", "Suresh Subramanian",
    # ECE Branch
    "Suhasini Kamat", "Vivek Marathe", "Mridula Kulkarni", "Omkar Deshpande", "Ketaki Godbole", "Anil Deshmukh",
    "Sunita Shinde", "Dilip Mane", "Rekha Patil", "Pramod Jadhav", "Vandana Bhosale", "Chetan Gaikwad",
    "Sharmila Sawant", "Shrikant Salvi", "Aparna More", "Ravindra Kadam", "Rohini Koli", "Vijay Tawde",
    "Smita Pawar", "Milind Rane", "Manisha Sathe", "Nilesh Thorat", "Pallavi Ghodke", "Sanjay Kute",
    # Additional pool for larger cohorts
    "Priya Sharma", "Karan Singh", "Neha Agarwal", "Raj Patel", "Anjali Verma", "Vicky Kumar", "Richa Sinha",
    "Amitabh Tiwari", "Poonam Devi", "Suresh Nair", "Kamala Harris", "Raghav Iyer", "Sita Ram", "Gopal Krishna",
    "Lakshmi Bai", "Narendra Modi", "Indira Gandhi", "Morarji Desai", "Atal Bihari", "Rajendra Prasad",
    "Abdul Kalam", "Homi Bhabha", "CV Raman", "Srinivasa Ramanujan", "Vikram Sarabhai", "Satish Dhawan",
]


def get_academic_dataset() -> Tuple[List[Course], List[Student], List[Room]]:
    """Generates the enterprise-scale academic dataset with 250+ students across 4 years."""

    # 1. Build Course Objects
    courses = [
        Course(
            id=c["id"],
            code=c["code"],
            name=c["name"],
            department=c["department"],
            credits=c["credits"],
            academic_year=c["academic_year"],
            semester=c["semester"],
            paper_code=c["paper_code"],
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

    # 3. Generate 250+ Students Across All 4 Academic Years
    students: List[Student] = []
    name_idx = 0

    def generate_prn(year: int, branch_code: str, roll: int) -> str:
        """Generate institutional PRN: YYYY{BRANCH}{XXX}"""
        year_code = 2027 - year  # 2024-2027 mapping
        return f"{year_code}{branch_code}{roll:03d}"

    # Year 1 - First Year (Sem 1-2) - 55 students
    year1_courses = {"FY101", "FY102", "FY103"}
    for i in range(1, 56):
        prn = generate_prn(1, "FY", i)
        name = STUDENT_NAME_POOL[name_idx % len(STUDENT_NAME_POOL)]
        name_idx += 1
        branch = random.choice(["CSE", "AIML", "DS", "IT", "ECE"])
        branch_code = "BCSE" if branch == "CSE" else ("BAIML" if branch == "AIML" else ("BDS" if branch == "DS" else ("BIT" if branch == "IT" else "BECE")))
        students.append(Student(
            id=f"2026{branch_code}{i:03d}",
            name=name,
            branch=branch,
            academic_year="First Year",
            semester=f"Semester {random.choice([1, 2])}",
            section=random.choice(["Section A", "Section B"]),
            enrolled_courses=year1_courses.copy(),
        ))

    # Year 2 - Second Year (Sem 3-4) - 60 students
    year2_core = {"SY201", "SY202"}
    for i in range(1, 61):
        prn = generate_prn(2, "SY", i)
        name = STUDENT_NAME_POOL[name_idx % len(STUDENT_NAME_POOL)]
        name_idx += 1
        branch = random.choice(["CSE", "AIML", "DS", "IT", "ECE"])
        branch_code = "BCSE" if branch == "CSE" else ("BAIML" if branch == "AIML" else ("BDS" if branch == "DS" else ("BIT" if branch == "IT" else "BECE")))
        elective = random.choice(["SY203", "SY202"])
        students.append(Student(
            id=f"2025{branch_code}{i:03d}",
            name=name,
            branch=branch,
            academic_year="Second Year",
            semester=f"Semester {random.choice([3, 4])}",
            section=random.choice(["Section A", "Section B"]),
            enrolled_courses=year2_core | {elective},
        ))

    # Year 3 - Third Year (Sem 5-6) - 70 students (CSE Section A/B, AIML, DS, IT, ECE)
    year3_core_cse = {"TY301", "TY302", "TY306"}
    year3_core_aiml = {"TY301", "TY303", "TY304"}
    year3_core_ds = {"TY302", "TY305", "TY306"}
    year3_core_it = {"TY301", "TY306", "TY302"}

    for i in range(1, 71):
        name = STUDENT_NAME_POOL[name_idx % len(STUDENT_NAME_POOL)]
        name_idx += 1

        if i <= 25:  # CSE Section A
            branch, sec = "CSE", "Section A"
            enrolled = year3_core_cse | {random.choice(["TY303", "TY305"])}
        elif i <= 50:  # CSE Section B
            branch, sec = "CSE", "Section B"
            enrolled = year3_core_cse | {random.choice(["TY303", "TY305"])}
        elif i <= 60:  # AIML
            branch, sec = "AI & ML", "Section A"
            enrolled = year3_core_aiml | {random.choice(["TY302", "TY306"])}
        elif i <= 65:  # Data Science
            branch, sec = "Data Science", "Section A"
            enrolled = year3_core_ds | {random.choice(["TY303", "TY301"])}
        elif i <= 68:  # IT
            branch, sec = "IT", "Section A"
            enrolled = year3_core_it | {random.choice(["TY303", "TY305"])}
        else:  # ECE
            branch, sec = "ECE", "Section A"
            enrolled = {"TY301", "TY306", "SY203"}

        branch_code = "BCSE" if branch == "CSE" else ("BAIML" if branch == "AI & ML" else ("BDS" if branch == "Data Science" else ("BIT" if branch == "IT" else "BECE")))
        students.append(Student(
            id=f"2024{branch_code}{(i%50)+1:03d}",
            name=name,
            branch=branch,
            academic_year="Third Year",
            semester=f"Semester {random.choice([5, 6])}",
            section=sec,
            enrolled_courses=enrolled,
        ))

    # Year 4 - Final Year (Sem 7-8) - 70 students
    year4_specializations = {
        "CSE": {"FY402", "FY403", "FY405"},
        "AI & ML": {"FY401", "FY403", "FY406"},
        "Data Science": {"FY405", "FY406", "FY401"},
        "IT": {"FY402", "FY405", "FY406"},
        "ECE": {"FY403", "FY404", "FY401"},
    }

    for i in range(1, 71):
        name = STUDENT_NAME_POOL[name_idx % len(STUDENT_NAME_POOL)]
        name_idx += 1

        branch = random.choice(["CSE", "AI & ML", "Data Science", "IT", "ECE"])
        sec = "Section A" if i <= 35 else "Section B"
        branch_code = "BCSE" if branch == "CSE" else ("BAIML" if branch == "AI & ML" else ("BDS" if branch == "Data Science" else ("BIT" if branch == "IT" else "BECE")))

        enrolled = year4_specializations[branch].copy()
        if random.random() > 0.5:
            enrolled.add(random.choice(list(year4_specializations[branch])))

        students.append(Student(
            id=f"2023{branch_code}{(i%50)+1:03d}",
            name=name,
            branch=branch,
            academic_year="Final Year",
            semester=f"Semester {random.choice([7, 8])}",
            section=sec,
            enrolled_courses=enrolled,
        ))

    # Register enrolled students into Course objects
    course_map = {c.id: c for c in courses}
    for stu in students:
        for cid in stu.enrolled_courses:
            if cid in course_map:
                course_map[cid].enrolled_students.add(stu.id)

    return courses, students, rooms


def export_dataset_to_csv(
    courses: Optional[List[Course]] = None,
    students: Optional[List[Student]] = None,
    rooms: Optional[List[Room]] = None,
    output_dir: Optional[str] = None,
) -> Tuple[str, str, str]:
    """Exports courses, students, and rooms to CSV files."""
    if output_dir is None:
        output_dir = DEFAULT_DATA_DIR

    if courses is None or students is None or rooms is None:
        courses, students, rooms = get_academic_dataset()

    os.makedirs(output_dir, exist_ok=True)
    courses_path = os.path.join(output_dir, "courses.csv")
    students_path = os.path.join(output_dir, "students.csv")
    rooms_path = os.path.join(output_dir, "rooms.csv")

    # Write courses.csv
    with open(courses_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "code", "name", "department", "credits", "academic_year", "semester", "paper_code"])
        for c in courses:
            writer.writerow([c.id, c.code, c.name, c.department, c.credits, c.academic_year, c.semester, c.paper_code])

    # Write students.csv
    with open(students_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "branch", "academic_year", "semester", "section", "enrolled_courses"])
        for s in students:
            writer.writerow([s.id, s.name, s.branch, s.academic_year, s.semester, s.section, ";".join(sorted(s.enrolled_courses))])

    # Write rooms.csv
    with open(rooms_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "capacity", "building", "room_type"])
        for r in rooms:
            writer.writerow([r.id, r.name, r.capacity, r.building, r.room_type])

    return courses_path, students_path, rooms_path


def load_dataset_from_csv(csv_dir: Optional[str] = None) -> Tuple[List[Course], List[Student], List[Room]]:
    """Loads dataset from CSV files."""
    if csv_dir is None:
        csv_dir = DEFAULT_DATA_DIR

    courses_path = os.path.join(csv_dir, "courses.csv")
    students_path = os.path.join(csv_dir, "students.csv")
    rooms_path = os.path.join(csv_dir, "rooms.csv")

    if not all(os.path.exists(p) for p in [courses_path, students_path, rooms_path]):
        export_dataset_to_csv(output_dir=csv_dir)

    courses = []
    with open(courses_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            courses.append(Course(
                id=row["id"], code=row["code"], name=row["name"],
                department=row.get("department", "Engineering"), credits=int(row.get("credits", 4)),
                academic_year=row.get("academic_year", "Third Year"), semester=row.get("semester", "Semester 5"),
                paper_code=row.get("paper_code", row["code"]),
            ))

    rooms = []
    with open(rooms_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rooms.append(Room(
                id=row["id"], name=row["name"], capacity=int(row["capacity"]),
                building=row.get("building", "Main Block"), room_type=row.get("room_type", "Exam Hall"),
            ))

    students = []
    course_map = {c.id: c for c in courses}
    with open(students_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            enrolled = {c.strip() for c in row["enrolled_courses"].split(";") if c.strip()}
            s = Student(
                id=row["id"], name=row["name"], branch=row.get("branch", "General"),
                academic_year=row.get("academic_year", "Third Year"), semester=row.get("semester", "Semester 5"),
                section=row.get("section", "Section A"), enrolled_courses=enrolled,
            )
            students.append(s)
            for cid in enrolled:
                if cid in course_map:
                    course_map[cid].enrolled_students.add(s.id)

    return courses, students, rooms


if __name__ == "__main__":
    c_p, s_p, r_p = export_dataset_to_csv()
    print(f"Generated enterprise CSVs in DAA PROJECT:\n - {c_p}\n - {s_p}\n - {r_p}")