import base64
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path


logger = logging.getLogger(__name__)


def _has_smtp_credentials() -> bool:
    return bool(os.getenv("SMTP_USERNAME") and os.getenv("SMTP_PASSWORD"))


def _build_message(
    *,
    to_email: str,
    from_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
    attachment_path: Path | None = None,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(text_body)

    if html_body:
        message.add_alternative(html_body, subtype="html")

    if attachment_path:
        with attachment_path.open("rb") as attachment_file:
            message.add_attachment(
                attachment_file.read(),
                maintype="application",
                subtype="pdf",
                filename=attachment_path.name,
            )

    return message


def _send_via_smtp(
    *,
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
    attachment_path: Path | None = None,
) -> dict:
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_timeout = int(os.getenv("SMTP_TIMEOUT", "30"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("EMAIL_FROM") or smtp_username
    smtp_debug = os.getenv("SMTP_DEBUG", "0").strip() == "1"

    if not smtp_username or not smtp_password:
        raise RuntimeError(
            "SMTP configuration missing. Set SMTP_USERNAME and SMTP_PASSWORD "
            "(use Gmail app password if using Gmail SMTP)."
        )

    if not from_email:
        raise RuntimeError("Missing sender email. Set EMAIL_FROM or SMTP_USERNAME.")

    logger.info(
        "Email attempt via SMTP | host=%s port=%s from=%s to=%s username_present=%s",
        smtp_host,
        smtp_port,
        from_email,
        to_email,
        bool(smtp_username),
    )

    message = _build_message(
        to_email=to_email,
        from_email=from_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        attachment_path=attachment_path,
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=smtp_timeout) as server:
        if smtp_debug:
            server.set_debuglevel(1)
        server.ehlo()
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
        server.login(smtp_username, smtp_password)
        send_failures = server.send_message(message)

    if send_failures:
        raise RuntimeError(f"SMTP recipient failures: {send_failures}")

    logger.info("Email delivered via SMTP to %s", to_email)
    return {"provider": "smtp", "to": to_email, "status": "sent"}


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
        attachment_bytes = attachment_path.read_bytes()
        payload["attachments"] = [
            {
                "filename": attachment_path.name,
                "content": base64.b64encode(attachment_bytes).decode("utf-8"),
            }
        ]

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
    """Send an email using provider configured for Render environment variables.

    Provider selection:
    - EMAIL_PROVIDER=resend: force Resend
    - EMAIL_PROVIDER=smtp: force SMTP
    - EMAIL_PROVIDER=auto (default): Resend if RESEND_API_KEY exists, otherwise SMTP
    """
    email_provider = os.getenv("EMAIL_PROVIDER", "auto").strip().lower()
    has_resend_key = bool(os.getenv("RESEND_API_KEY"))
    has_smtp_creds = _has_smtp_credentials()

    logger.info(
        "Preparing email send | provider=%s to=%s subject=%s attachment=%s has_resend_key=%s has_smtp_creds=%s",
        email_provider,
        to_email,
        subject,
        str(attachment_path) if attachment_path else "none",
        has_resend_key,
        has_smtp_creds,
    )

    try:
        if email_provider == "resend":
            if not has_resend_key and has_smtp_creds:
                logger.warning(
                    "EMAIL_PROVIDER=resend but RESEND_API_KEY missing. Falling back to SMTP."
                )
                return _send_via_smtp(
                    to_email=to_email,
                    subject=subject,
                    text_body=text_body,
                    html_body=html_body,
                    attachment_path=attachment_path,
                )
            return _send_via_resend(
                to_email=to_email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                attachment_path=attachment_path,
            )

        if email_provider == "smtp":
            if not has_smtp_creds and has_resend_key:
                logger.warning(
                    "EMAIL_PROVIDER=smtp but SMTP credentials missing. Falling back to Resend."
                )
                return _send_via_resend(
                    to_email=to_email,
                    subject=subject,
                    text_body=text_body,
                    html_body=html_body,
                    attachment_path=attachment_path,
                )
            return _send_via_smtp(
                to_email=to_email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                attachment_path=attachment_path,
            )

        if email_provider not in {"auto", "smtp", "resend"}:
            logger.warning(
                "Unknown EMAIL_PROVIDER value '%s'. Using auto selection.",
                email_provider,
            )

        if has_resend_key:
            return _send_via_resend(
                to_email=to_email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                attachment_path=attachment_path,
            )

        if not has_smtp_creds:
            raise RuntimeError(
                "No valid email provider configuration found. "
                "Set RESEND_API_KEY (+ EMAIL_FROM) or SMTP_USERNAME/SMTP_PASSWORD (+ EMAIL_FROM)."
            )

        return _send_via_smtp(
            to_email=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            attachment_path=attachment_path,
        )
    except Exception as exc:
        logger.exception(
            "Email send failed | provider=%s to=%s subject=%s",
            email_provider,
            to_email,
            subject,
        )
        raise RuntimeError(str(exc)) from exc
