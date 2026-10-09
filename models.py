"""
models.py
---------
Core Domain Models and Data Structures for Intelligent Exam Timetable Scheduling.

Defines entities: Course, Student, Room, TimeSlot, and Assignment representations
used throughout the graph builder, optimization engines, and validation layers.
"""

from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional, Any


@dataclass
class Course:
    """Represents an academic course (Graph Vertex)."""
    id: str
    code: str
    name: str
    department: str = "CSE"
    credits: int = 4
    enrolled_students: Set[str] = field(default_factory=set)

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
    branch: str = "CSE"
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
class TimeSlot:
    """Represents a distinct exam time slot (Color in Graph Coloring)."""
    id: int
    day: int
    session: str  # e.g., 'Morning' or 'Afternoon'
    label: str

    def __hash__(self):
        return hash(self.id)


@dataclass
class ExamAssignment:
    """Represents a scheduled course with its assigned time slot and rooms."""
    course_id: str
    slot_id: int
    rooms: List[str]
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


@dataclass
class ScheduleResult:
    """Complete output payload returned by scheduling algorithms."""
    course_to_slot: Dict[str, int]
    slot_to_courses: Dict[int, List[str]]
    room_allocations: Dict[str, List[str]]  # course_id -> list of room_ids
    metrics: ScheduleMetrics
    is_feasible: bool
    details: Dict[str, Any] = field(default_factory=dict)
