"""
hall_ticket_pdf.py
------------------
Official Hall Ticket PDF Generator (fpdf2 / FPDF) — clean institutional layout.
"""
from typing import List
from fpdf import FPDF
from models import StudentSeatAssignment, Student


class HallTicketPDF(FPDF):
    def header(self):
        self.set_fill_color(30, 58, 138)
        self.set_draw_color(30, 58, 138)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 15)
        self.cell(0, 9, "VISHWAKARMA UNIVERSITY  |  EXAMINATION CELL", 0, 1, "C", fill=True)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "OFFICIAL UNIVERSITY EXAMINATION ADMISSION CARD  |  HALL TICKET", 0, 1, "C")
        self.set_draw_color(30, 58, 138)
        self.set_line_width(0.6)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(180, 180, 180)
        self.set_text_color(120, 120, 120)
        self.set_font("Helvetica", "I", 6.5)
        self.cell(0, 8, f"Official Document - University Examination Cell | Page {self.page_no()} | Confidential - Not for redistribution",
                    0, 0, "C")


def generate_official_hall_ticket_pdf(
    student: Student,
    assignments: List[StudentSeatAssignment],
    exam_block_start: str = "2026-11-16",
) -> bytes:
    pdf = HallTicketPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    # === STUDENT BIO BOX (clean bordered single box, two-column internal layout) ===
    y_start = pdf.get_y()
    pdf.set_fill_color(245, 247, 250)
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(0.7)
    pdf.rect(10, y_start, 190, 36, style="DF")

    # Photo placeholder (left, inside box)
    pdf.set_xy(14, y_start + 2)
    pdf.set_fill_color(220, 225, 235)
    pdf.rect(14, y_start + 2, 42, 28, style="DF")
    pdf.set_xy(14, y_start + 12)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(42, 5, "STUDENT PHOTO / ID", 0, 1, "C")
    pdf.set_font("Helvetica", "I", 6.5)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(42, 5, "[Institutional ID / QR Placeholder]", 0, 1, "C")

    # Bio fields (right, aligned cleanly)
    pdf.set_xy(62, y_start + 2)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(30, 58, 138)

    field_rows = [
        ("NAME", student.name),
        ("INSTITUTIONAL PRN", student.id),
        ("BRANCH / COHORT", student.branch),
        ("ACADEMIC LEVEL", f"{student.academic_year}  |  {student.semester}"),
        ("SECTION", student.section),
    ]
    for label, value in field_rows:
        # Label
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(60, 60, 60)
        pdf.set_x(62)
        pdf.cell(28, 5, f"{label}:", 0, 0, "L")
        # Value
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(10, 10, 10)
        pdf.cell(95, 5, str(value), 0, 1, "L")

    pdf.ln(3)

    # === EXAMINATION TIMETABLE (clean narrow-table with auto-wrap) ===
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 7, "EXAMINATION TIMETABLE", 0, 1, "L")
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    # Compact header
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 6.5)
    col_w = [26, 30, 22, 22, 36, 44]
    headers = ["Date", "Time Window", "Session", "Code", "Course Title", "Room / Seat"]
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 6, h, 1, 0, "C", fill=True)
    pdf.ln()

    # Rows with wrapping
    pdf.set_text_color(20, 20, 20)
    pdf.set_font("Helvetica", "", 6.5)

    for idx, assignment in enumerate(sorted(assignments, key=lambda a: a.slot_id)):
        fill = (idx % 2 == 1)
        pdf.set_fill_color(240, 244, 250) if fill else pdf.set_fill_color(255, 255, 255)

        # Date (wrap allowed if long)
        pdf.set_xy(10, pdf.get_y())
        pdf.cell(col_w[0], 6, assignment.calendar_date, 1, 0, "L", fill=fill)
        # Time
        pdf.cell(col_w[1], 6, assignment.time_window, 1, 0, "L", fill=fill)
        # Session
        pdf.cell(col_w[2], 6, assignment.session_name[:14], 1, 0, "L", fill=fill)
        # Course code
        pdf.cell(col_w[3], 6, assignment.course_code, 1, 0, "C", fill=fill)
        # Course title (truncate long)
        pdf.cell(col_w[4], 6, assignment.course_title[:30], 1, 0, "L", fill=fill)
        # Room / Seat
        room_seat = f"{assignment.room_name} / {assignment.seat_label}"
        pdf.cell(col_w[5], 6, room_seat[:36], 1, 1, "L", fill=fill)

    # Ensure enough space before footnotes/signature
    pdf.ln(3)

    # === INSTRUCTIONS ===
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 6, "INVIGILATOR & CANDIDATE INSTRUCTIONS", 0, 1, "L")

    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(40, 40, 40)
    instructions = [
        "1. Report to examination hall 30 minutes before scheduled exam time.",
        "2. Mandatory College ID / University PRN verification at entry.",
        "3. Only permitted writing instruments allowed; electronic devices strictly prohibited.",
        "4. No communication with other candidates; violation = disqualification.",
        "5. Occupy assigned seat per this Hall Ticket; seat change requires Controller permission.",
        "6. Submit all examination papers before leaving hall; time is strictly enforced.",
    ]
    for instr in instructions:
        pdf.set_x(10)
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(5, 5, "-", 0, 0)
        pdf.multi_cell(0, 4.5, instr)
    pdf.ln(2)

    # === SIGNATURE BLOCKS (clear separation) ===
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 6, "AUTHORIZATION & SIGNATURES", 0, 1, "L")

    sig_y = pdf.get_y()
    # Student box (left)
    pdf.set_draw_color(120, 120, 120)
    pdf.rect(10, sig_y, 85, 18, style="D")
    pdf.set_xy(10, sig_y + 2)
    pdf.set_font("Helvetica", "B", 7)
    pdf.cell(85, 5, "STUDENT SIGNATURE", 0, 1)
    pdf.set_xy(10, sig_y + 10)
    pdf.set_font("Helvetica", "I", 6.5)
    pdf.cell(85, 5, f"Name: {student.name}  |  PRN: {student.id}", 0, 1)

    # Controller box (right)
    pdf.rect(105, sig_y, 85, 18, style="D")
    pdf.set_xy(105, sig_y + 2)
    pdf.set_font("Helvetica", "B", 7)
    pdf.cell(85, 5, "CONTROLLER OF EXAMINATIONS", 0, 1)
    pdf.set_xy(105, sig_y + 10)
    pdf.set_font("Helvetica", "I", 6.5)
    pdf.cell(85, 5, "Name: Prof. Dr. University Controller  |  Signature: _______________", 0, 1)

    pdf.ln(6)

    # Bottom seal line
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(0.4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Helvetica", "I", 6)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, "Vishwakarma University - Examination Cell | Official University Document - Confidential", 0, 1, "C")

    pdf_output = pdf.output(dest="S")
    if isinstance(pdf_output, bytearray):
        return bytes(pdf_output)
    if isinstance(pdf_output, str):
        return pdf_output.encode("latin-1")
    return bytes(pdf_output)
