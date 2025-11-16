# worker/verifier/score_engine.py

def compute_score(checks: dict) -> int:
    score = 0

    if not checks.get("syntax_ok"):
        return 0
    score += 10

    if checks.get("domain_exists"):
        score += 10

    if checks.get("mx_exists"):
        score += 10

    if checks.get("disposable"):
        score -= 10
    else:
        score += 10

    if checks.get("role_based"):
        score -= 5
    else:
        score += 5

    if checks.get("catch_all"):
        score += 5
    else:
        score += 10

    smtp_status = checks.get("smtp_status")

    if smtp_status == "accept":
        score += 40
    elif smtp_status == "greylist":
        score += 20
    elif smtp_status == "reject":
        score += 0
    else:
        score += 10

    return max(0, min(score, 100))
