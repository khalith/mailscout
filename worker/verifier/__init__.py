# worker/verifier/__init__.py

from .syntax_engine import (
    normalize_email,
    is_syntax_valid,
)

from .disposable import is_disposable
from .dns_engine import resolve_mx_for_domain
from .smtp_engine import smtp_check_rcpt
from .catchall_checker import is_catch_all
from .provider_profiles import identify_provider
from .score_engine import compute_score_and_status

__all__ = [
    "normalize_email",
    "is_syntax_valid",
    "is_disposable",
    "resolve_mx_for_domain",
    "smtp_check_rcpt",
    "is_catch_all",
    "identify_provider",
    "compute_score_and_status",
]
