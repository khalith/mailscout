# worker/verifier/smtp_engine.py
import asyncio
from aiosmtplib import SMTP, SMTPException
from typing import Tuple, Optional

# Non-intrusive SMTP RCPT check:
# connect -> HELO/EHLO -> MAIL FROM -> RCPT TO -> QUIT
# NOTE: observe provider throttling and aggressive timeouts.

async def smtp_check_rcpt(mx_host: str, target_email: str, mail_from: str = "verify@localhost", timeout: float = 8.0) -> Tuple[bool, Optional[str]]:
    """
    Try non-intrusive RCPT TO check against an MX host.
    Returns (accepted:boolean, reason:str|null)
    If connection fails or times out -> (False, "error")
    """
    if not mx_host or not target_email:
        return False, "invalid-args"

    try:
        smtp = SMTP(hostname=mx_host, timeout=timeout)
        await smtp.connect()
        # EHLO/HELO
        try:
            await smtp.ehlo_or_helo_if_needed()
        except Exception:
            pass

        # MAIL FROM
        try:
            resp = await smtp.mail(mail_from)
        except SMTPException:
            # some servers fail MAIL FROM, treat as unknown
            await smtp.quit()
            return False, "mail-from-reject"

        # RCPT TO
        try:
            code, message = await smtp.rcpt(target_email)
            # codes 250 and 251 usually mean accepted; 550/551 banned
            accepted = int(code) >= 200 and int(code) < 400
            await smtp.quit()
            return accepted, f"{code} {message.decode() if isinstance(message, bytes) else message}"
        except SMTPException as e:
            try:
                await smtp.quit()
            except Exception:
                pass
            return False, f"rcpt-exception:{str(e)}"
    except asyncio.TimeoutError:
        return False, "timeout"
    except Exception as e:
        return False, f"connect-exception:{str(e)}"
