# worker/verifier/dns_checker.py
import dns.asyncresolver

resolver = dns.asyncresolver.Resolver()

async def resolve_mx(domain: str):
    try:
        answers = await resolver.resolve(domain, "MX")
        mx = sorted([(r.preference, r.exchange.to_text()) for r in answers], key=lambda x: x[0])
        return [h for _, h in mx]
    except Exception:
        # Try A fallback
        try:
            a = await resolver.resolve(domain, "A")
            return [a[0].to_text()]
        except:
            return []
