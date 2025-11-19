# worker/verifier/score_engine.py
from typing import Dict, Any, Tuple

def compute_score_and_status(
    syntax_ok: bool,
    disposable: bool,
    mx_hosts: list,
    smtp_accept: bool | None,
    catch_all: bool,
    provider: str | None
) -> Tuple[int, str, Dict[str, Any]]:
    """
    Return: (score 0-100, status string, details dict)
    Status: valid / risky / invalid
    Heuristic scoring — conservative.
    """
    score = 0
    details = {
        "syntax": syntax_ok,
        "disposable": disposable,
        "mx_count": len(mx_hosts or []),
        "smtp_accept": smtp_accept,
        "catch_all": catch_all,
        "provider": provider,
    }

    if not syntax_ok:
        return 0, "invalid", details

    # base for syntax OK
    score = 30

    # disposable reduces score heavily
    if disposable:
        score = min(score, 10)

    # MX presence boosts score
    if mx_hosts and len(mx_hosts) > 0:
        score += 30

    # SMTP acceptance best signal
    if smtp_accept is True:
        score += 30
    elif smtp_accept is False:
        # rejected explicitly
        score = min(score, 20)

    # catch-all reduces confidence
    if catch_all:
        score = max(10, score - 20)

    # provider adjustments
    if provider == "gmail":
        # gmail often accepts; but we trust it slightly more
        score = min(100, score + 5)

    # clamp
    score = max(0, min(100, score))

    status = "risky"
    if score >= 75:
        status = "valid"
    elif score <= 20:
        status = "invalid"
    else:
        status = "risky"

    return int(score), status, details
