from collections import Counter
from datetime import datetime, time, timedelta
from statistics import median

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from .models import RequestEvent
from .workflow import REVIEW_PERMISSION, Status, catalog_labels, visible_requests


PERIODS = (7, 30, 90)
DECISIONS = (Status.APPROVED, Status.REJECTED)


def p90(values):
    ordered = sorted(values)
    rank = 0.9 * (len(ordered) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (rank - lower) * (ordered[upper] - ordered[lower])


def duration_label(seconds):
    minutes = int(seconds // 60)
    if not minutes:
        return "< 1 min"
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days:
        return f"{days} j {hours} h"
    if hours:
        return f"{hours} h {minutes:02d} min"
    return f"{minutes} min"


def build_buckets(first_day, period, daily):
    step = {7: 1, 30: 5, 90: 10}[period]
    buckets = []
    for offset in range(0, period, step):
        days = range(offset, min(offset + step, period))
        dates = [first_day + timedelta(days=day) for day in days]
        submitted = sum(daily[day, Status.SUBMITTED] for day in dates)
        decided = sum(daily[day, status] for day in dates for status in DECISIONS)
        buckets.append({
            "start": dates[0],
            "end": dates[-1],
            "submitted": submitted,
            "decided": decided,
        })
    peak = max(1, *(max(row["submitted"], row["decided"]) for row in buckets))
    for row in buckets:
        row["submitted_height"] = round(100 * row["submitted"] / peak)
        row["decided_height"] = round(100 * row["decided"] / peak)
    return buckets, peak


@never_cache
@login_required
@require_safe
def dashboard(request):
    chosen = request.GET.get("period", "30")
    period = next((days for days in PERIODS if str(days) == chosen), 30)
    today = timezone.localdate()
    first_day = today - timedelta(days=period - 1)
    zone = timezone.get_current_timezone()
    begin = datetime.combine(first_day, time.min, zone)
    end = datetime.combine(today + timedelta(days=1), time.min, zone)

    records = visible_requests(request.user)
    events = RequestEvent.objects.filter(
        request_id__in=records.order_by().values("pk"),
        created_at__gte=begin, created_at__lt=end,
    )
    counts = events.order_by().annotate(day=TruncDate("created_at", tzinfo=zone)).values(
        "day", "status",
    ).annotate(total=Count("pk"))
    daily = Counter({(row["day"], row["status"]): row["total"] for row in counts})
    totals = Counter()
    for (_, status), count in daily.items():
        totals[status] += count
    decided = sum(totals[status] for status in DECISIONS)

    submission = RequestEvent.objects.filter(
        request_id=OuterRef("request_id"), status=Status.SUBMITTED,
    ).order_by("created_at").values("created_at")[:1]
    durations = [
        (finished - started).total_seconds()
        for finished, started in events.filter(status__in=DECISIONS).annotate(
            started=Subquery(submission),
        ).values_list("created_at", "started").iterator()
        if started is not None and finished >= started
    ]
    buckets, peak = build_buckets(first_day, period, daily)
    log = Paginator(events.select_related("actor", "request").order_by("-created_at", "-id"), 15)
    page = log.get_page(request.GET.get("page"))

    return render(request, "workflow/activity.html", {
        "current_view": "activity",
        "current_label": "Activité",
        "reviewer": request.user.has_perm(REVIEW_PERMISSION),
        "periods": PERIODS,
        "period": period,
        "first_day": first_day,
        "today": today,
        "submitted": totals[Status.SUBMITTED],
        "decided": decided,
        "approved": totals[Status.APPROVED],
        "approval_rate": 100 * totals[Status.APPROVED] / decided if decided else None,
        "pending": records.filter(status=Status.SUBMITTED).count(),
        "sample": len(durations),
        "median_delay": duration_label(median(durations)) if durations else "—",
        "p90_delay": duration_label(p90(durations)) if durations else "—",
        "buckets": buckets,
        "peak": peak,
        "log_page": page,
        "log_rows": [(event, *catalog_labels(event.request)) for event in page],
    })
