# worker/verifier/catchall_checker.py
import random
import string
import asyncio
from typing import List
from .dns_engine import resolve_mx_for_domain
from .smtp_engine import smtp_check_rcpt

async def is_catch_all(domain: str, mail_from: str = "verify@localhost") -> bool:
    """
    Detect catch-all behavior using one random address + a known good address pattern.
    Strategy:
      - resolve MX
      - pick top MX host(s)
      - try RCPT TO for a clearly-random address
      - if server accepts random -> likely catch-all
    This is heuristic and must be conservative.
    """
    if not domain:
        return False

    mxs = await resolve_mx_for_domain(domain)
    if not mxs:
        return False

    # generate a random-looking address unlikely to exist
    rand_local = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
    test_addr = f"{rand_local}@{domain}"

    # probe up to first 2 MX hosts with short timeouts
    for mx in mxs[:2]:
        try:
            accepted, _ = await smtp_check_rcpt(mx, test_addr, mail_from=mail_from, timeout=6.0)
            if accepted:
                # if random accepted — treat as catch-all (conservative)
                return True
        except Exception:
            continue
    return False
