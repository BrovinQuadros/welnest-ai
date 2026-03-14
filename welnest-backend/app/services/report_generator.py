from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.ai_service import summarize_text
from app.database import journals_collection, moods_collection


BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def _mood_label(score: int) -> str:
    if score >= 8:
        return "Happy"
    if score >= 6:
        return "Neutral"
    if score >= 4:
        return "Anxious"
    return "Sad"


def _calculate_mood_summary(moods: List[dict]) -> Dict[str, int]:
    summary = {"Happy": 0, "Neutral": 0, "Sad": 0, "Anxious": 0}
    for mood in moods:
        label = _mood_label(int(mood.get("mood_score", 0)))
        summary[label] += 1
    return summary


def _report_period(moods: List[dict], journals: List[dict]) -> str:
    all_dates = []
    for item in moods + journals:
        created_at = item.get("created_at")
        if isinstance(created_at, datetime):
            all_dates.append(created_at)

    if not all_dates:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return f"{today} to {today}"

    start = min(all_dates).strftime("%Y-%m-%d")
    end = max(all_dates).strftime("%Y-%m-%d")
    return f"{start} to {end}"


def _build_chart(user_id: str, moods: List[dict]) -> Path | None:
    if not moods:
        return None

    try:
        import matplotlib.pyplot as plt
    except Exception:
        # Keep report generation resilient even if matplotlib isn't installed yet.
        return None

    day_scores: Dict[str, List[int]] = {}
    for mood in moods:
        created_at = mood.get("created_at")
        if not isinstance(created_at, datetime):
            continue
        day = created_at.strftime("%Y-%m-%d")
        day_scores.setdefault(day, []).append(int(mood.get("mood_score", 0)))

    if not day_scores:
        return None

    labels = sorted(day_scores.keys())
    values = [sum(day_scores[d]) / len(day_scores[d]) for d in labels]

    chart_path = REPORT_DIR / f"{user_id}_mood_trend.png"
    plt.figure(figsize=(8, 3.2))
    plt.plot(labels, values, marker="o", linewidth=2, color="#4f46e5")
    plt.title("Mood Trend Over Time")
    plt.xlabel("Date")
    plt.ylabel("Average Mood Score")
    plt.ylim(1, 10)
    plt.grid(alpha=0.3)
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(chart_path, dpi=150)
    plt.close()
    return chart_path


def _journaling_stats(journals: List[dict]) -> Tuple[int, float]:
    total_entries = len(journals)
    if total_entries == 0:
        return 0, 0.0

    dates = [j.get("created_at") for j in journals if isinstance(j.get("created_at"), datetime)]
    if not dates:
        return total_entries, 0.0

    days_span = max((max(dates) - min(dates)).days + 1, 1)
    weeks = max(days_span / 7, 1)
    avg_per_week = round(total_entries / weeks, 2)
    return total_entries, avg_per_week


def _build_ai_insight(moods: List[dict], journals: List[dict]) -> str:
    if not moods and not journals:
        return "Not enough data available to generate AI insight."

    mood_summary = _calculate_mood_summary(moods)
    total_journals = len(journals)
    prompt = (
        "Generate one short wellness insight (1-2 sentences) based on this user summary: "
        f"Mood counts: {mood_summary}. Total journal entries: {total_journals}. "
        "Mention practical patterns without medical claims."
    )
    return summarize_text(prompt)


def _build_coping_strategies(moods: List[dict]) -> List[str]:
    if not moods:
        return [
            "Try a 2-minute breathing exercise to settle your mind.",
            "Take a short walk outdoors for a gentle mood reset.",
            "Practice 5 minutes of mindfulness meditation.",
        ]

    scores = [int(m.get("mood_score", 0)) for m in moods if m.get("mood_score") is not None]
    avg = sum(scores) / len(scores) if scores else 0
    labels = Counter(_mood_label(s) for s in scores)

    strategies = []
    if labels.get("Anxious", 0) > 0:
        strategies.append("Use box breathing (4-4-4-4) for 3 rounds during anxious moments.")
    if labels.get("Sad", 0) > 0:
        strategies.append("Schedule a short outdoor walk and note one positive moment afterwards.")
    if avg < 6:
        strategies.append("Set a small daily routine: hydration, movement, and a brief journal reflection.")

    strategies.extend([
        "Practice 5-10 minutes of mindfulness meditation before bedtime.",
        "Reach out to a trusted friend or family member for social support.",
    ])

    # Keep the section concise and non-repetitive
    deduped = []
    for strategy in strategies:
        if strategy not in deduped:
            deduped.append(strategy)
    return deduped[:5]


async def get_report_status(user_id: str) -> Dict[str, int | bool]:
    journal_count = await journals_collection.count_documents({"username": user_id})
    mood_count = await moods_collection.count_documents({"username": user_id})
    return {
        "has_journal_data": journal_count > 0,
        "journal_entries": journal_count,
        "mood_entries": mood_count,
    }


async def generate_pdf_report(user_id: str) -> Path:
    moods = await moods_collection.find({"username": user_id}).sort("created_at", 1).to_list(1000)
    journals = await journals_collection.find({"username": user_id}).sort("created_at", 1).to_list(1000)

    file_path = REPORT_DIR / f"{user_id}_wellness_report.pdf"
    chart_path = _build_chart(user_id, moods)

    mood_summary = _calculate_mood_summary(moods)
    total_entries, avg_per_week = _journaling_stats(journals)
    ai_insight = _build_ai_insight(moods, journals)
    coping_strategies = _build_coping_strategies(moods)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=8,
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#111827"),
        spaceBefore=8,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
    )

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=1.6 * cm,
        leftMargin=1.6 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
    )

    story = [
        Paragraph("WellNest Wellness Report", title_style),
        Paragraph(f"<b>Username:</b> {user_id}", body_style),
        Paragraph(f"<b>Generated on:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", body_style),
        Paragraph(f"<b>Report period:</b> {_report_period(moods, journals)}", body_style),
        Spacer(1, 12),
    ]

    story.append(Paragraph("Mood Summary", section_style))
    mood_table = Table(
        [["Mood", "Count"]] + [[label, count] for label, count in mood_summary.items()],
        colWidths=[8 * cm, 4 * cm],
    )
    mood_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([mood_table, Spacer(1, 12)])

    story.append(Paragraph("Mood Trend Visualization", section_style))
    if chart_path and chart_path.exists():
        story.append(Image(str(chart_path), width=17 * cm, height=7 * cm))
    else:
        story.append(Paragraph("No mood data available to build trend chart.", body_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Journaling Statistics", section_style))
    story.append(Paragraph(f"Total entries: <b>{total_entries}</b>", body_style))
    story.append(Paragraph(f"Average entries per week: <b>{avg_per_week}</b>", body_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Journal Entries", section_style))
    if journals:
        for entry in journals:
            created_at = entry.get("created_at")
            date_text = created_at.strftime("%Y-%m-%d") if isinstance(created_at, datetime) else "Unknown date"
            content = (entry.get("content") or "").replace("\n", "<br/>")
            story.append(Paragraph(f"<b>Date:</b> {date_text}", body_style))
            story.append(Paragraph(content, body_style))
            story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("No journal entries available for this period.", body_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("AI Insights", section_style))
    story.append(Paragraph(ai_insight, body_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Recommended Coping Strategies", section_style))
    for strategy in coping_strategies:
        story.append(Paragraph(f"• {strategy}", body_style))

    doc.build(story)

    if chart_path and chart_path.exists():
        chart_path.unlink(missing_ok=True)

    return file_path


async def generate_csv_report(user_id: str) -> Path:
    moods = await moods_collection.find({"username": user_id}).sort("created_at", 1).to_list(1000)
    journals = await journals_collection.find({"username": user_id}).sort("created_at", 1).to_list(1000)

    file_path = REPORT_DIR / f"{user_id}_wellness_data.csv"

    rows = []
    for mood in moods:
        created_at = mood.get("created_at")
        score = mood.get("mood_score")
        rows.append({
            "date": created_at.isoformat() if isinstance(created_at, datetime) else "",
            "record_type": "mood",
            "mood_score": score,
            "mood_label": _mood_label(int(score)) if score is not None else "",
            "notes": mood.get("notes", ""),
            "journal_entry": "",
        })

    for journal in journals:
        created_at = journal.get("created_at")
        rows.append({
            "date": created_at.isoformat() if isinstance(created_at, datetime) else "",
            "record_type": "journal",
            "mood_score": "",
            "mood_label": "",
            "notes": "",
            "journal_entry": journal.get("content", ""),
        })

    rows.sort(key=lambda item: item["date"])

    with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["date", "record_type", "mood_score", "mood_label", "notes", "journal_entry"],
        )
        writer.writeheader()
        writer.writerows(rows)

    return file_path