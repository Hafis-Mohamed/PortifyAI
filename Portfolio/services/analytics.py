"""
PortifyAI visitor analytics.

Every visit to a deployed portfolio is stored in the local database in two ways:
  1. A raw `PortfolioView` row (audit log: device, referer, hashed visitor id, time).
  2. Aggregate counters on `Portfolio` (`view_count`, `unique_visitor_count`,
     `last_viewed_at`) that are incremented atomically, so dashboards never
     need to scan the whole log.
"""
import hashlib
import ipaddress
import json
from datetime import timedelta
from urllib.parse import urlparse

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from Portfolio.models import Portfolio, PortfolioView

# Ignore repeat hits from the same visitor within this window (double-fired
# beacons, back/forward cache restores, rapid refreshes).
DEDUPE_WINDOW = timedelta(seconds=10)

BOT_MARKERS = (
    "bot", "crawler", "spider", "slurp", "crawl", "preview", "facebookexternalhit",
    "whatsapp", "telegram", "discord", "headless", "lighthouse", "pingdom",
    "uptime", "monitor", "curl", "wget", "python-requests", "vercel", "httpclient",
)

LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def get_client_ip(request):
    """Return a valid client IP (first X-Forwarded-For hop, else REMOTE_ADDR) or None."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    candidates = [ip.strip() for ip in forwarded.split(",") if ip.strip()]
    candidates.append(request.META.get("REMOTE_ADDR", ""))
    for candidate in candidates:
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError:
            continue
    return None


def is_bot(user_agent):
    if not user_agent:
        return True
    ua = user_agent.lower()
    return any(marker in ua for marker in BOT_MARKERS)


def detect_device(user_agent):
    ua = (user_agent or "").lower()
    # Tablets must be checked first: iPad UAs also contain "Mobile".
    if "ipad" in ua or "tablet" in ua or ("android" in ua and "mobile" not in ua):
        return "Tablet"
    if "mobile" in ua or "iphone" in ua or "android" in ua:
        return "Mobile"
    return "Desktop"


def make_visitor_hash(ip, user_agent):
    """Salted, one-way visitor id so raw IPs aren't needed to count uniques."""
    raw = f"{settings.SECRET_KEY}:{ip or ''}:{(user_agent or '')[:200]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def record_visit(request, username):
    """
    Store a visit for `username`'s portfolio.
    Returns the Portfolio (or None if not found). Bots and duplicate hits are ignored.
    """
    portfolio = Portfolio.objects.filter(user__username__iexact=username).first()
    if not portfolio:
        return None

    user_agent = request.META.get("HTTP_USER_AGENT", "")
    if is_bot(user_agent):
        return portfolio

    # The portfolio owner previewing their own site shouldn't inflate stats.
    if request.user.is_authenticated and request.user.pk == portfolio.user_id:
        return portfolio

    ip = get_client_ip(request)
    visitor_hash = make_visitor_hash(ip, user_agent)
    referer = (request.GET.get("ref") or request.META.get("HTTP_REFERER") or "Direct Link")[:250]
    now = timezone.now()

    with transaction.atomic():
        visitor_views = PortfolioView.objects.filter(portfolio=portfolio, visitor_hash=visitor_hash)
        if visitor_views.filter(created_at__gte=now - DEDUPE_WINDOW).exists():
            return portfolio
        is_new_visitor = not visitor_views.exists()

        PortfolioView.objects.create(
            portfolio=portfolio,
            ip_address=ip,
            user_agent=user_agent[:500],
            visitor_hash=visitor_hash,
            referer=referer,
            device_type=detect_device(user_agent),
        )

        # Atomic counter update (QuerySet.update skips auto_now on updated_at).
        Portfolio.objects.filter(pk=portfolio.pk).update(
            view_count=F("view_count") + 1,
            unique_visitor_count=F("unique_visitor_count") + (1 if is_new_visitor else 0),
            last_viewed_at=now,
        )

    portfolio.refresh_from_db(fields=["view_count", "unique_visitor_count", "last_viewed_at"])
    return portfolio


def get_tracking_base(request=None):
    """Public base URL that deployed portfolios should send beacons to."""
    base = getattr(settings, "TRACKING_BASE_URL", "") or ""
    if not base and request is not None:
        base = request.build_absolute_uri("/")
    return base.rstrip("/")


def is_public_base(base_url):
    """False for localhost / private IPs, which visitors' browsers can never reach."""
    host = (urlparse(base_url).hostname or "").lower()
    if not host or host in LOCAL_HOSTS:
        return False
    try:
        return not ipaddress.ip_address(host).is_private
    except ValueError:
        return True


def build_tracking_snippet(username, tracking_base):
    """JS beacon injected into the deployed portfolio HTML."""
    endpoint = json.dumps(f"{tracking_base}/track/{username}/")
    return f"""
    <!-- PortifyAI Visitor Analytics -->
    <script>
        (function () {{
            try {{
                var ref = encodeURIComponent(document.referrer || 'Direct Link');
                var img = new Image(1, 1);
                img.referrerPolicy = 'no-referrer-when-downgrade';
                img.src = {endpoint} + '?ref=' + ref + '&t=' + Date.now();
            }} catch (e) {{}}
        }})();
    </script>
    """
