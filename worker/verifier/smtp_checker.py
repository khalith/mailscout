# worker/verifier/smtp_checker.py
import aiosmtplib
import async_timeout
import asyncio
from utils.mx_limiter import get_mx_semaphore

SMTP_TIMEOUT = 8
MAIL_FROM = "check@mailscout.local"

async def smtp_check(mx_host: str, email: str, per_mx_limit: int):
    sem = await get_mx_semaphore(mx_host, per_mx_limit)

    async with sem:
        try:
            async with async_timeout.timeout(SMTP_TIMEOUT):
                smtp = aiosmtplib.SMTP(hostname=mx_host, timeout=SMTP_TIMEOUT)
                await smtp.connect()
                await smtp.helo("mailscout.local")
                await smtp.mail(MAIL_FROM)
                code, resp = await smtp.rcpt(email)
                await smtp.quit()

                return {
                    "code": code,
                    "message": resp.decode() if isinstance(resp, bytes) else resp
                }

        except Exception as e:
            return {"code": None, "message": str(e)}
