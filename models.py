"""
models.py
---------
Core Domain Models and Data Structures for Intelligent Exam Timetable Scheduling.

Defines entities: Course, Student, Room, TimeSlot, RoomSeatAllocation, and Assignment
representations used throughout the graph builder, optimization engines, and validation layers.
"""

from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional, Any


@dataclass
class Course:
    """Represents an academic course (Graph Vertex)."""
    id: str
    code: str
    name: str
    department: str = "Computer Science & Engineering"
    credits: int = 4
    academic_year: str = "Year 3"
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
    """Represents a student enrolled across multiple courses."""
    id: str
    name: str
    branch: str = "Computer Science & Engineering"
    academic_year: str = "Year 3"
    semester: str = "Semester 5"
    section: str = "Section A"
    enrolled_courses: Set[str] = field(default_factory=set)

    def __hash__(self):
        return hash(self.id)


@dataclass
class Room:
    """Represents an examination hall with seating capacity."""
    id: str
    name: str
    capacity: int
    building: str = "Main Block"
    room_type: str = "Exam Hall"

    def __hash__(self):
        return hash(self.id)


@dataclass
class RoomSeatAllocation:
    """Detailed seating distribution of a course within a specific examination hall."""
    room_id: str
    room_name: str
    capacity: int
    allocated_seats: int

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
class ExamAssignment:
    """Represents a scheduled course with its assigned time slot and rooms."""
    course_id: str
    slot_id: int
    rooms: List[str]
    seat_allocations: List[RoomSeatAllocation]
    student_count: int


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


@dataclass
class ScheduleResult:
    """Complete output payload returned by scheduling algorithms."""
    course_to_slot: Dict[str, int]
    slot_to_courses: Dict[int, List[str]]
    room_allocations: Dict[str, List[str]]                         # course_id -> list of room_ids
    room_allocation_details: Dict[str, List[RoomSeatAllocation]]   # course_id -> detailed room allocations
    time_slots: Dict[int, TimeSlot]                                # slot_id -> TimeSlot metadata
    metrics: ScheduleMetrics
    is_feasible: bool
    details: Dict[str, Any] = field(default_factory=dict)
