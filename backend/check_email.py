"""Check that the backend can send email through the configured SMTP account (Gmail).

Run from the backend folder:

    .venv\\Scripts\\python.exe check_email.py              # test the login only
    .venv\\Scripts\\python.exe check_email.py you@gmail.com   # also send a test message

The password is never printed.
"""
import smtplib
import ssl
import sys
from email.message import EmailMessage

from app.database.database import settings

GMAIL_HELP = """
Gmail rejected the username or password (error 535). Gmail does not accept your normal
account password for SMTP. To fix it:

  1. Turn on 2-Step Verification: https://myaccount.google.com/security
  2. Create an App Password:       https://myaccount.google.com/apppasswords
  3. Put the 16-character code in SMTP_PASSWORD in the .env file (spaces are ignored).
  4. Make sure SMTP_USERNAME and SMTP_FROM_EMAIL are that same Gmail address.
  5. Restart the backend and run this check again.
"""


def main() -> int:
    recipient = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"SMTP host:     {settings.smtp_host}:{settings.smtp_port} "
          f"({'SSL' if settings.smtp_use_ssl else 'STARTTLS' if settings.smtp_use_starttls else 'plain'})")
    print(f"SMTP username: {settings.smtp_username or '(not set)'}")
    print(f"From address:  {settings.smtp_from_email or '(not set)'}")
    print(f"Password set:  {'yes' if settings.smtp_password else 'no'}")
    if not (settings.smtp_host and settings.smtp_from_email):
        print("\nSMTP_HOST and SMTP_FROM_EMAIL must be set in .env.")
        return 1

    password = settings.smtp_password.replace(" ", "")
    stage = "connect"
    try:
        if settings.smtp_use_ssl:
            smtp = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20, context=ssl.create_default_context())
        else:
            smtp = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20)
            if settings.smtp_use_starttls:
                smtp.starttls(context=ssl.create_default_context())
        with smtp:
            if settings.smtp_username:
                stage = "login"
                smtp.login(settings.smtp_username, password)
            stage = "send"
            print("\nLogin: OK")
            if recipient:
                message = EmailMessage()
                message["Subject"] = "AlumniConnect email check"
                message["From"] = settings.smtp_from_email
                message["To"] = recipient
                message.set_content("This is a test message from AlumniConnect. Sign-in codes will arrive like this.")
                smtp.send_message(message)
                print(f"Test message sent to {recipient}. Check the inbox (and spam).")
        return 0
    except smtplib.SMTPAuthenticationError as error:
        print(f"\nLogin: FAILED ({error.smtp_code})")
        if "gmail" in settings.smtp_host.lower():
            print(GMAIL_HELP)
        return 2
    except smtplib.SMTPServerDisconnected as error:
        # After a 535 Gmail often closes the connection before Python can report it,
        # so a disconnect during login almost always means the credentials were refused.
        if stage == "login" and "gmail" in settings.smtp_host.lower():
            print("\nLogin: FAILED (Gmail closed the connection after the login attempt)")
            print(GMAIL_HELP)
            return 2
        print(f"\nCould not send: {type(error).__name__}: {error}")
        return 3
    except Exception as error:  # noqa: BLE001 - this is a diagnostic tool
        print(f"\nCould not send: {type(error).__name__}: {error}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
