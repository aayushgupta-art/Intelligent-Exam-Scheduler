"""
seating_allocator.py (continued) / hall_ticket_pdf.py
--------------------------------------------------------
Official Hall Ticket PDF Generator using fpdf2 (FPDF).
Produces institutional-grade examination admission cards.
"""

from typing import List
from fpdf import FPDF
from models import StudentSeatAssignment, Student


class HallTicketPDF(FPDF):
    """Custom FPDF subclass for institutional hall ticket layout."""

    def header(self):
        # University header banner
        self.set_fill_color(30, 58, 138)  # Deep navy blue
        self.set_draw_color(30, 58, 138)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "VISHWAKARMA UNIVERSITY  |  EXAMINATION CELL", 0, 1, "C", fill=True)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "OFFICIAL UNIVERSITY EXAMINATION ADMISSION CARD", 0, 1, "C")
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(180, 180, 180)
        self.set_text_color(100, 100, 100)
        self.set_font("Helvetica", "I", 7)
        self.cell(0, 10, f"Official Document - University Examination Cell | Page {self.page_no()} | Confidential", 0, 0, "C")


def generate_official_hall_ticket_pdf(
    student: Student,
    assignments: List[StudentSeatAssignment],
    exam_block_start: str = "2026-11-16",
) -> bytes:
    """Generates a professional PDF hall ticket and returns bytes for download."""
    pdf = HallTicketPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ---- Student Bio Box (Two-column structured) ----
    pdf.set_fill_color(240, 245, 250)
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(0.8)
    pdf.rect(10, pdf.get_y(), 190, 38, style="DF")

    # Left column: Photo placeholder + PRN
    pdf.set_xy(14, pdf.get_y() + 2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(55, 6, "STUDENT PHOTO / ID", 0, 1)
    pdf.set_fill_color(220, 230, 240)
    pdf.set_draw_color(30, 58, 138)
    pdf.rect(14, pdf.get_y(), 48, 22, style="DF")
    pdf.set_xy(14, pdf.get_y() + 7)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(48, 5, "[Institutional Photo / QR Code\nPlaceholder]", 0, 1, "C")

    # Right column: Bio fields
    pdf.set_xy(72, pdf.get_y() - 26)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 58, 138)

    fields = [
        ("NAME", student.name),
        ("INSTITUTIONAL PRN", student.id),
        ("BRANCH / COHORT", student.branch),
        ("ACADEMIC LEVEL", f"{student.academic_year}  |  {student.semester}"),
        ("SECTION", student.section),
    ]

    for label, value in fields:
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(35, 5, f"{label}:", 0, 0)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(85, 5, str(value), 0, 1)

    pdf.ln(4)

    # ---- Examination Timetable Table ----
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 7, "EXAMINATION TIMETABLE", 0, 1, "L")
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    # Table header
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 7.5)
    col_w = [30, 32, 28, 28, 28, 44]
    headers = ["Date", "Time Window", "Session", "Course", "Course Title", "Room / Seat"]
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 7, h, 1, 0, "C", fill=True)
    pdf.ln()

    # Table rows
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_fill_color(245, 245, 245)

    for assignment in sorted(assignments, key=lambda a: a.slot_id):
        # Alternate row shading
        fill = False
        if assignments.index(assignment) % 2 == 1:
            fill = True

        pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)

        # Date
        pdf.cell(col_w[0], 7, assignment.calendar_date, 1, 0, "L", fill=fill)
        # Time
        pdf.cell(col_w[1], 7, assignment.time_window, 1, 0, "L", fill=fill)
        # Session
        pdf.cell(col_w[2], 7, assignment.session_name, 1, 0, "L", fill=fill)
        # Course code
        pdf.cell(col_w[3], 7, assignment.course_code, 1, 0, "C", fill=fill)
        # Course title (truncate if needed)
        title_text = assignment.course_title[:28]
        pdf.cell(col_w[4], 7, title_text, 1, 0, "L", fill=fill)
        # Room / Seat
        room_seat = f"{assignment.room_name} / {assignment.seat_label}"
        pdf.cell(col_w[5], 7, room_seat, 1, 1, "L", fill=fill)

    pdf.ln(4)

    # ---- Instructions Footer ----
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(1.0)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 6, "INVIGILATOR & CANDIDATE INSTRUCTIONS", 0, 1, "L")

    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(40, 40, 40)
    instructions = [
        "1. Candidates must report at the examination hall 30 minutes before the scheduled exam time.",
        "2. Mandatory College ID Card / University PRN verification required at entry.",
        "3. Only permitted writing instruments (blue/black pen, pencil for rough) allowed.",
        "4. Electronic devices (phones, smartwatches, calculators with memory) are strictly prohibited.",
        "5. No communication with other candidates during examination; violation results in disqualification.",
        "6. Candidate must occupy the assigned seat as per this Hall Ticket; seat change requires Controller permission.",
        "7. All examination papers must be submitted before leaving the hall; time is strictly enforced.",
    ]
    for instr in instructions:
        pdf.set_x(10)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.cell(5, 5, "-", 0, 0)
        pdf.multi_cell(0, 5, instr)
    pdf.ln(2)

    # ---- Signature Blocks ----
    pdf.set_draw_color(30, 58, 138)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 6, "AUTHORIZATION & SIGNATURES", 0, 1, "L")

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)

    # Two-column signature layout
    sig_y = pdf.get_y()
    # Student signature box
    pdf.set_draw_color(120, 120, 120)
    pdf.rect(10, sig_y, 85, 18, style="D")
    pdf.set_xy(10, sig_y + 2)
    pdf.set_font("Helvetica", "B", 7)
    pdf.cell(85, 5, "STUDENT SIGNATURE", 0, 1)
    pdf.set_xy(10, sig_y + 10)
    pdf.set_font("Helvetica", "I", 7)
    pdf.cell(85, 5, f"Name: {student.name}  |  PRN: {student.id}", 0, 1)

    # Controller signature box
    pdf.rect(105, sig_y, 85, 18, style="D")
    pdf.set_xy(105, sig_y + 2)
    pdf.set_font("Helvetica", "B", 7)
    pdf.cell(85, 5, "CONTROLLER OF EXAMINATIONS", 0, 1)
    pdf.set_xy(105, sig_y + 10)
    pdf.set_font("Helvetica", "I", 7)
    pdf.cell(85, 5, "Name: Prof. Dr. University Controller  |  Signature: _______________", 0, 1)

    pdf.ln(6)

    # Bottom institutional seal text
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Helvetica", "I", 6)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, "Vishwakarma University - Examination Cell | Official University Document - Not for redistribution without Controller authorization.", 0, 1, "C")

    # Return PDF bytes
    return pdf.output()
