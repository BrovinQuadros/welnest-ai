import base64
import logging
import os
from pathlib import Path


logger = logging.getLogger(__name__)


def _send_via_resend(
    *,
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
    attachment_path: Path | None = None,
) -> dict:
    resend_api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("EMAIL_FROM")

    if not resend_api_key:
        raise RuntimeError("Missing RESEND_API_KEY for Resend email delivery.")

    if not from_email:
        raise RuntimeError("Missing EMAIL_FROM for Resend email delivery.")

    try:
        import resend
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Resend SDK not installed. Install with: pip install resend"
        ) from exc

    resend.api_key = resend_api_key

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "text": text_body,
    }

    if html_body:
        payload["html"] = html_body

    if attachment_path:
        attachment_exists = os.path.exists(attachment_path)
        logger.info(
            "Attachment check before send | path=%s exists=%s",
            str(attachment_path),
            attachment_exists,
        )
        if attachment_exists:
            attachment_bytes = attachment_path.read_bytes()
            payload["attachments"] = [
                {
                    "filename": attachment_path.name,
                    "content": base64.b64encode(attachment_bytes).decode("utf-8"),
                }
            ]
        else:
            logger.warning(
                "Attachment file not found at %s. Sending email without attachment.",
                str(attachment_path),
            )

    logger.info("Email attempt via Resend | from=%s to=%s", from_email, to_email)
    response = resend.Emails.send(payload)
    logger.info("Email delivered via Resend to %s | response=%s", to_email, response)

    return {"provider": "resend", "to": to_email, "status": "sent", "response": response}


def send_email(
    *,
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
    attachment_path: Path | None = None,
) -> dict:
    """Send an email using Resend configured via environment variables on Render."""
    raw_email_provider = os.getenv("EMAIL_PROVIDER")
    email_provider = (raw_email_provider or "").strip().lower()

    logger.info(
        "Preparing email send | EMAIL_PROVIDER(raw)=%s EMAIL_PROVIDER(normalized)=%s to=%s subject=%s attachment=%s",
        raw_email_provider,
        email_provider,
        to_email,
        subject,
        str(attachment_path) if attachment_path else "none",
    )

    try:
        if email_provider == "resend":
            return _send_via_resend(
                to_email=to_email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                attachment_path=attachment_path,
            )

        raise RuntimeError(
            "No valid email provider configuration found. "
            f"Expected EMAIL_PROVIDER='resend', got '{raw_email_provider}'."
        )
    except Exception as exc:
        logger.exception(
            "Email send failed | provider=%s to=%s subject=%s",
            email_provider,
            to_email,
            subject,
        )
        raise RuntimeError(str(exc)) from exc
