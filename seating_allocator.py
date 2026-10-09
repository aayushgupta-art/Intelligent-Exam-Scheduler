"""
seating_allocator.py
--------------------
Room-Wise Seating Allocation Engine for Enterprise Exam Scheduling.

Maps enrolled students to specific physical seats/benches in assigned examination halls,
generates attendance manifests for invigilators, and creates printable admit cards.

Implements:
1. Student-to-Seat Mapping: PRN + Name -> Seat Label (e.g., 'AUD-S001', 'LH101-D015')
2. Attendance Manifests: Per-room, per-slot records for invigilator sign-off
3. Individual Admit Cards: Student-specific timetable with seating assignments
"""

from typing import Dict, List, Tuple, Set
from models import (
    Course, Student, Room, StudentSeatAssignment, RoomSeatAllocation,
    ExamManifest, ScheduleResult, TimeSlot
)


class SeatingAllocator:
    """Intelligently maps students to physical seats across examination venues."""

    def __init__(
        self,
        courses: List[Course],
        students: List[Student],
        rooms: List[Room],
        schedule: ScheduleResult,
    ):
        self.courses = courses
        self.students = students
        self.rooms = rooms
        self.schedule = schedule
        self.course_map = {c.id: c for c in courses}
        self.student_map = {s.id: s for s in students}
        self.room_map = {r.id: r for r in rooms}

    def allocate_seats(self) -> Tuple[Dict[str, List[StudentSeatAssignment]], Dict[Tuple[int, str], List[StudentSeatAssignment]]]:
        """
        Allocates students to specific seats in assigned rooms.

        Returns:
        - student_seating_manifests: course_id -> list of StudentSeatAssignment
        - room_manifests: (slot_id, room_id) -> list of StudentSeatAssignment
        """
        student_seating_manifests: Dict[str, List[StudentSeatAssignment]] = {}
        room_manifests: Dict[Tuple[int, str], List[StudentSeatAssignment]] = {}

        # Iterate through each course's assigned rooms and seating
        for course_id, room_allocations in self.schedule.room_allocation_details.items():
            course_obj = self.course_map.get(course_id)
            if not course_obj:
                continue

            slot_id = self.schedule.course_to_slot.get(course_id)
            if slot_id is None:
                continue

            slot_meta = self.schedule.time_slots.get(slot_id, TimeSlot(slot_id, 0, "", "", "", "", "", "", ""))

            # Get all students enrolled in this course
            enrolled_student_ids = list(course_obj.enrolled_students)
            enrolled_students = [self.student_map[sid] for sid in enrolled_student_ids if sid in self.student_map]

            # Sort students by PRN for deterministic seating
            enrolled_students.sort(key=lambda s: s.id)

            seat_assignments = []
            global_seat_index = 1

            # Allocate students to rooms according to room_allocation_details
            for room_alloc in room_allocations:
                room_obj = self.room_map.get(room_alloc.room_id)
                if not room_obj:
                    continue

                allocated_seats = room_alloc.allocated_seats

                # Extract students for this room
                students_for_room = enrolled_students[
                    sum(r.allocated_seats for r in room_allocations[:room_allocations.index(room_alloc)]) :
                    sum(r.allocated_seats for r in room_allocations[:room_allocations.index(room_alloc) + 1])
                ]

                # Generate seat labels and assignments
                for seat_offset, stu in enumerate(students_for_room, 1):
                    seat_label = self._generate_seat_label(room_obj.id, seat_offset)

                    assignment = StudentSeatAssignment(
                        seat_number=global_seat_index,
                        seat_label=seat_label,
                        student_id=stu.id,
                        student_name=stu.name,
                        branch=stu.branch,
                        academic_year=stu.academic_year,
                        course_id=course_id,
                        course_code=course_obj.code,
                        course_title=course_obj.name,
                        room_id=room_obj.id,
                        room_name=room_obj.name,
                        slot_id=slot_id,
                        calendar_date=slot_meta.calendar_date,
                        time_window=slot_meta.time_window,
                        session_name=slot_meta.session_name,
                    )

                    seat_assignments.append(assignment)
                    global_seat_index += 1

                    # Track in room manifest
                    manifest_key = (slot_id, room_obj.id)
                    if manifest_key not in room_manifests:
                        room_manifests[manifest_key] = []
                    room_manifests[manifest_key].append(assignment)

            student_seating_manifests[course_id] = seat_assignments

        return student_seating_manifests, room_manifests

    def _generate_seat_label(self, room_id: str, seat_offset: int) -> str:
        """Generate human-readable seat label: e.g., 'AUD-S001', 'LH101-D015'."""
        room_prefix = room_id.split("_")[0][:3].upper()
        return f"{room_prefix}-S{seat_offset:03d}"

    def generate_room_manifests(self) -> Dict[Tuple[int, str], ExamManifest]:
        """Generates official examination room attendance manifests for invigilators."""
        _, room_assignments = self.allocate_seats()

        manifests: Dict[Tuple[int, str], ExamManifest] = {}

        for (slot_id, room_id), student_rows in room_assignments.items():
            room_obj = self.room_map.get(room_id)
            slot_meta = self.schedule.time_slots.get(slot_id)

            if not room_obj or not slot_meta:
                continue

            # Aggregate unique courses in this room/slot
            course_codes = list(set(row.course_code for row in student_rows))

            # Derive formatted date from calendar_date
            try:
                from datetime import datetime
                fd = datetime.strptime(slot_meta.calendar_date, "%Y-%m-%d").strftime("%A, %d %b %Y")
            except Exception:
                fd = slot_meta.calendar_date

            manifest = ExamManifest(
                slot_id=slot_id,
                room_id=room_id,
                room_name=room_obj.name,
                calendar_date=slot_meta.calendar_date,
                formatted_date=fd,
                time_window=slot_meta.time_window,
                session_name=slot_meta.session_name,
                total_students=len(student_rows),
                course_codes=sorted(course_codes),
                student_rows=sorted(student_rows, key=lambda r: r.seat_label),
            )

            manifests[(slot_id, room_id)] = manifest

        return manifests

    def generate_student_admit_cards(self) -> Dict[str, List[StudentSeatAssignment]]:
        """Generates individual student admit cards with their scheduled exams and seat assignments."""
        student_cards: Dict[str, List[StudentSeatAssignment]] = {}

        _, room_assignments = self.allocate_seats()

        for student_rows in room_assignments.values():
            for assignment in student_rows:
                if assignment.student_id not in student_cards:
                    student_cards[assignment.student_id] = []
                student_cards[assignment.student_id].append(assignment)

        # Sort each student's exams by slot_id for chronological timetable
        for student_id in student_cards:
            student_cards[student_id].sort(key=lambda a: a.slot_id)

        return student_cards
