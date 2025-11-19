# worker/verifier/dns_engine.py
import aiodns
import asyncio
from typing import List

# You may supply alternate resolvers by passing nameservers to aiodns.DNSResolver
resolver = aiodns.DNSResolver()

async def resolve_mx_for_domain(domain: str, timeout: float = 5.0) -> List[str]:
    """
    Return ordered list of mx hostnames (strings).
    If none or error -> return [].
    """
    if not domain:
        return []
    try:
        fut = resolver.query(domain, "MX")
        records = await asyncio.wait_for(fut, timeout=timeout)
        # records: list of objects with .priority and .host
        mxs = sorted(((r.priority, r.host.rstrip(".")) for r in records), key=lambda x: x[0])
        return [host for _, host in mxs]
    except aiodns.error.DNSError:
        return []
    except asyncio.TimeoutError:
        return []
    except Exception:
        return []
