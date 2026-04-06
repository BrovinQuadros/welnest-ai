from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.auth_dependencies import get_current_user
from app.database import report_shares_collection
from app.models import ShareReportRequest
from app.services.email_service import send_email
from app.services.report_generator import (
    generate_csv_report,
    generate_pdf_report,
    get_report_status,
)


router = APIRouter(tags=["Reports"])
logger = logging.getLogger(__name__)


@router.get("/api/report/status")
async def report_status(current_user: str = Depends(get_current_user)):
    return await get_report_status(current_user)


# ============================================================
# CSV EXPORT - WELLNESS DATA
# New endpoint + backward compatibility endpoint
# ============================================================
@router.get("/api/report/csv")
@router.get("/export/csv")
async def export_wellness_csv(current_user: str = Depends(get_current_user)):
    try:
        file_path = await generate_csv_report(current_user)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate CSV report")

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="text/csv",
    )


# ============================================================
# PDF EXPORT - WELLNESS REPORT
# New endpoint + backward compatibility endpoint
# ============================================================
@router.get("/api/report/pdf")
@router.get("/export/pdf")
async def export_wellness_pdf(current_user: str = Depends(get_current_user)):
    status = await get_report_status(current_user)
    if not status.get("has_journal_data"):
        raise HTTPException(status_code=404, detail="No journal data found")

    try:
        file_path = await generate_pdf_report(current_user)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/pdf",
    )


@router.post("/api/report/share")
async def share_wellness_report(
    payload: ShareReportRequest,
    current_user: str = Depends(get_current_user)
):
    provider_email = payload.provider_email.strip().lower()

    if not provider_email:
        raise HTTPException(status_code=400, detail="Provider email is required")

    try:
        logger.info(
            "Share report requested | user=%s provider_email=%s",
            current_user,
            provider_email,
        )

        report_path = await generate_pdf_report(current_user)

        email_subject = f"WellNest Wellness Report - {current_user}"
        email_text = (
            f"Hello,\n\n"
            f"{current_user} has shared their wellness report with you. "
            f"Please find the attached PDF report.\n\n"
            f"Sent via WellNest AI."
        )
        email_html = (
            "<p>Hello,</p>"
            f"<p><strong>{current_user}</strong> has shared their wellness report with you.</p>"
            "<p>Please find the attached PDF report.</p>"
            "<p>Sent via WellNest AI.</p>"
        )

        send_result = send_email(
            to_email=provider_email,
            subject=email_subject,
            text_body=email_text,
            html_body=email_html,
            attachment_path=report_path,
        )

        logger.info(
            "Share report email sent successfully | user=%s provider_email=%s provider=%s",
            current_user,
            provider_email,
            send_result.get("provider"),
        )

        await report_shares_collection.insert_one(
            {
                "username": current_user,
                "provider_email": provider_email,
                "report_file": report_path.name,
                "shared_at": datetime.utcnow(),
                "status": "sent",
                "email_provider": send_result.get("provider"),
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to share report for user '%s'", current_user)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to share report: {str(exc)}",
        )

    return {
        "message": "Report shared successfully",
        "provider_email": provider_email,
        "status": "sent",
        "delivery": send_result,
    }