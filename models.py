"""
models.py
---------
Core Domain Models and Data Structures for Enterprise University Exam Scheduling.

Defines entities: Course, Student, Room, TimeSlot, RoomSeatAllocation, StudentSeatAssignment,
ExamManifest, and ScheduleResult representations used throughout the graph builder,
optimization engines, seating allocation, and validation layers.
"""

from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional, Any, Tuple


@dataclass
class Course:
    """Represents an academic course (Graph Vertex)."""
    id: str
    code: str
    name: str
    department: str = "Computer Science & Engineering"
    credits: int = 4
    academic_year: str = "Third Year"
    semester: str = "Semester 5"
    paper_code: str = ""  # For Anti-Paper-Leak synchronization (defaults to code)
    enrolled_students: Set[str] = field(default_factory=set)

    def __post_init__(self):
        if not self.paper_code:
            self.paper_code = self.code

    @property
    def student_count(self) -> int:
        return len(self.enrolled_students)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, Course):
            return self.id == other.id
        return False


@dataclass
class Student:
    """Represents a student enrolled across multiple courses with institutional PRN."""
    id: str  # Institutional PRN (e.g., '2024BCSE001', '2025BIT015')
    name: str
    branch: str = "Computer Science & Engineering"
    academic_year: str = "Third Year"
    semester: str = "Semester 5"
    section: str = "Section A"
    enrolled_courses: Set[str] = field(default_factory=set)

    def __hash__(self):
        return hash(self.id)


@dataclass
class Room:
    """Represents an examination hall or computer lab with physical seating capacity."""
    id: str
    name: str
    capacity: int
    building: str = "Main Academic Complex"
    room_type: str = "Exam Hall"

    def __hash__(self):
        return hash(self.id)


@dataclass
class StudentSeatAssignment:
    """Specific physical desk/bench assignment for a student during an examination session."""
    seat_number: int            # Numeric seat index: 1, 2, 3...
    seat_label: str             # e.g., 'AUD-S001', 'LH101-D015'
    student_id: str             # PRN
    student_name: str
    branch: str
    academic_year: str
    course_id: str
    course_code: str
    course_title: str
    room_id: str
    room_name: str
    slot_id: int
    calendar_date: str = ""
    time_window: str = ""


@dataclass
class RoomSeatAllocation:
    """Detailed seating distribution of a course within a specific examination hall."""
    room_id: str
    room_name: str
    capacity: int
    allocated_seats: int
    student_assignments: List[StudentSeatAssignment] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.allocated_seats <= self.capacity


@dataclass
class TimeSlot:
    """Represents a distinct exam time slot with calendar date and exact clock time window."""
    id: int
    day_index: int
    calendar_date: str          # e.g., '2026-11-16'
    formatted_date: str         # e.g., 'Monday, 16 Nov 2026'
    session_name: str           # e.g., 'Morning Session'
    start_time: str             # e.g., '09:30 AM'
    end_time: str               # e.g., '12:30 PM'
    time_window: str            # e.g., '09:30 AM - 12:30 PM'
    label: str                  # e.g., 'Slot #1: 16-Nov-2026 (09:30 AM - 12:30 PM)'

    def __hash__(self):
        return hash(self.id)


@dataclass
class ExamManifest:
    """Official Examination Room Attendance Manifest for invigilators."""
    slot_id: int
    room_id: str
    room_name: str
    calendar_date: str
    time_window: str
    session_name: str
    total_students: int
    course_codes: List[str]
    student_rows: List[StudentSeatAssignment]
    invigilator_name: str = "Dr. Senior Faculty Invigilator"


@dataclass
class ScheduleMetrics:
    """Stores performance metrics and constraint evaluations of a generated schedule."""
    total_slots_used: int
    chromatic_number_estimate: int
    student_conflict_count: int
    room_capacity_violations: int
    consecutive_exam_penalties: int
    same_day_exam_penalties: int
    slot_distribution_variance: float
    execution_time_ms: float
    algorithm_used: str
    calendar_days_spanned: int = 0
    synchronized_papers_count: int = 0
    paper_leak_vulnerabilities: int = 0
    multi_room_splits_count: int = 0
    total_seats_allocated: int = 0
    total_manifests_generated: int = 0


@dataclass
class ScheduleResult:
    """Complete output payload returned by scheduling algorithms."""
    course_to_slot: Dict[str, int]
    slot_to_courses: Dict[int, List[str]]
    room_allocations: Dict[str, List[str]]                                   # course_id -> list of room_ids
    room_allocation_details: Dict[str, List[RoomSeatAllocation]]             # course_id -> detailed room allocations
    student_seating_manifests: Dict[str, List[StudentSeatAssignment]]         # course_id -> list of student seat allocations
    room_manifests: Dict[Tuple[int, str], List[StudentSeatAssignment]]        # (slot_id, room_id) -> list of student seat allocations
    time_slots: Dict[int, TimeSlot]                                          # slot_id -> TimeSlot metadata
    metrics: ScheduleMetrics
    is_feasible: bool
    details: Dict[str, Any] = field(default_factory=dict)
