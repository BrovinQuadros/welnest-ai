from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from app.database import get_db
from app.auth_dependencies import get_current_user

import csv
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

router = APIRouter(prefix="/report", tags=["Reports"])

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)

# ---------- CSV EXPORT (MOODS) ----------
@router.get("/csv")
def export_mood_csv(current_user: str = Depends(get_current_user)):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT mood_score, notes, created_at
        FROM moods
        WHERE username = ?
        ORDER BY created_at
        """,
        (current_user,)
    )

    rows = cursor.fetchall()
    db.close()

    file_path = REPORT_DIR / f"{current_user}_mood_report.csv"

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Mood Score", "Notes", "Date"])
        writer.writerows(rows)

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="text/csv"
    )


# ---------- PDF EXPORT (JOURNAL) ----------
@router.get("/pdf")
def export_journal_pdf(current_user: str = Depends(get_current_user)):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT content, created_at
        FROM journals
        WHERE username = ?
        ORDER BY created_at
        """,
        (current_user,)
    )

    rows = cursor.fetchall()
    db.close()

    file_path = REPORT_DIR / f"{current_user}_journal_report.pdf"

    c = canvas.Canvas(str(file_path), pagesize=A4)
    width, height = A4
    y = height - 40

    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Journal Report for {current_user}")
    y -= 30

    for content, created_at in rows:
        if y < 80:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - 40

        c.drawString(40, y, f"Date: {created_at}")
        y -= 15

        text = c.beginText(40, y)
        for line in content.split("\n"):
            text.textLine(line)
            y -= 14
        c.drawText(text)
        y -= 20

    c.save()

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/pdf"
    )
