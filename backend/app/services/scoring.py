# backend/app/services/scoring.py
# Simple wrapper to compute score from checks dict using the previously defined model.
def compute_score(checks: dict) -> int:
    # checks keys expected:
    # syntax_ok, domain_exists, mx_exists, disposable, role_based, catch_all, smtp_status, smtp_code
    score = 0
    # syntax
    if not checks.get("syntax_ok", False):
        return 0
    score += 10
    # domain
    if checks.get("domain_exists", False):
        score += 10
    # mx
    if checks.get("mx_exists", False):
        score += 10
    else:
        score += 0
    # disposable
    if checks.get("disposable", False):
        score -= 10
    else:
        score += 10
    # role
    if checks.get("role_based", False):
        score -= 5
    else:
        score += 5
    # catch_all
    if checks.get("catch_all", False):
        score += 5
    else:
        score += 10
    # smtp
    smtp_status = checks.get("smtp_status", "")
    if smtp_status == "accept":
        score += 40
    elif smtp_status == "greylist":
        score += 20
    elif smtp_status == "reject":
        score += 0
    else:
        score += 10
    # clamp 0-100
    if score < 0:
        score = 0
    if score > 100:
        score = 100
    return score
