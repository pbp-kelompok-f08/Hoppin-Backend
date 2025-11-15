from django.db import connection
from django.db.models import Count, F, Q
from django.db.utils import OperationalError, ProgrammingError
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from liveChat.models import Group
from accounts.models import CustomUser  
import json, uuid
from django.utils import timezone
from datetime import timedelta




from .forms import MatchForm, MatchSearchForm, ParticipationForm
from .models import Match, Participation, SportCategory


DEFAULT_CATEGORIES = [
    "Sepak Bola", "Basket", "Bulu Tangkis", "Futsal", "Lari", "Bersepeda", "Other"
]


def _is_schema_ready() -> bool:
    """Check whether the tables required for the match feature exist."""
    try:
        existing_tables = set(connection.introspection.table_names())
    except (OperationalError, ProgrammingError):
        return False

    required_tables = {
        SportCategory._meta.db_table,
        Match._meta.db_table,
        Participation._meta.db_table,
    }
    return required_tables.issubset(existing_tables)


def _ensure_default_categories() -> None:
    if not _is_schema_ready():
        return

    for name in DEFAULT_CATEGORIES:
        SportCategory.objects.get_or_create(name=name)


def _serialize_match(match: Match) -> dict:
    return {
        "id": match.id,
        "title": match.title,
        "category": match.category.name,
        "category_slug": match.category.slug,
        "location": match.location,
        "event_date": match.event_date.isoformat(),
        "description": match.description,
        "max_members": match.max_members,
        "current_members": match.current_members,
        "available_slots": match.available_slots,
    }


@require_http_methods(["GET"])
def match_dashboard(request):
    print("DEBUG SPORT FILTER:", request.GET.get("sport"))
    schema_ready = _is_schema_ready()

    if not schema_ready:
        categories = []
        total_matches = Match.objects.count()
        today_matches = Match.objects.filter(event_date__date=timezone.now().date()).count()
        total_players = Participation.objects.values('user').distinct().count()
        sports_count = SportCategory.objects.count()

        popular_sports = (
            SportCategory.objects.annotate(match_count=Count("matches"))
            .order_by("-match_count")[:3]
        )
        recent_activity = Match.objects.select_related("category").order_by("-id")[:5]

        context = {
            "schema_ready": False,
            "grouped_matches": [],
            "match_form": MatchForm(),
            "participation_form": ParticipationForm(),
            "search_form": MatchSearchForm(),
            "has_any_match": False,
            "categories": categories,
            "total_matches": total_matches,
            "today_matches": today_matches,
            "total_players": total_players,
            "sports_count": sports_count,
            "popular_sports": popular_sports,
            "recent_activity": recent_activity,
            "players_online": 0,
            "players_active_today": 0,
        }

        return render(request, "matches/dashboard.html", context, status=503)

    _ensure_default_categories()

    matches = (
        Match.objects.select_related("category")
        .annotate(participant_count=Count("participations"))
        .order_by("event_date")
    )

    search_form = MatchSearchForm(request.GET or None)
    if search_form.is_valid():
        category = search_form.cleaned_data.get("category")
        keyword = search_form.cleaned_data.get("keyword")
        available_only = search_form.cleaned_data.get("available_only")

        sport_value = request.GET.get("sport")
        if sport_value:
            matches = matches.filter(category__slug__iexact=sport_value)

        when_value = request.GET.get("when")
        today = timezone.now().date()
        if when_value == "today":
            matches = matches.filter(event_date__date=today)
        elif when_value == "week":
            matches = matches.filter(event_date__date__range=(today, today + timedelta(days=7)))
        elif when_value == "month":
            matches = matches.filter(event_date__date__range=(today, today + timedelta(days=30)))

        if category:
            matches = matches.filter(category=category)
        if keyword:
            matches = matches.filter(
                Q(title__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(location__icontains=keyword)
            )
        if available_only:
            matches = matches.filter(participant_count__lt=F("max_members"))

    match_list = list(matches)
    categories = list(SportCategory.objects.all().order_by('name'))
    categories = sorted(categories, key=lambda c: c.name == "Other")

    grouped_matches = [
        (category, [m for m in match_list if m.category == category])
        for category in categories
    ]
    has_any_match = any(matches for _, matches in grouped_matches)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        payload = []
        for category, items in grouped_matches:
            if not items:
                continue
            payload.append(
                {
                    "category": category.name,
                    "category_slug": category.slug,
                    "matches": [_serialize_match(match) for match in items],
                }
            )
        return JsonResponse({"groups": payload})
    
    now = timezone.now()
    today = now.date()
    ten_minutes_ago = now - timedelta(minutes=10)

    total_matches = Match.objects.count()
    today_matches = Match.objects.filter(event_date__date=today).count()
    total_players = Participation.objects.values('user').distinct().count()
    sports_count = SportCategory.objects.count()

    players_online = CustomUser.objects.filter(last_activity__gte=ten_minutes_ago).distinct().count()
    players_active_today = CustomUser.objects.filter(last_activity__date=today).distinct().count()

    popular_sports = (
        SportCategory.objects.annotate(match_count=Count("matches"))
        .order_by("-match_count")[:3]
    )

    recent_activity = Match.objects.select_related("category").order_by("-id")[:5]

    context = {
        "grouped_matches": grouped_matches,
        "match_form": MatchForm(),
        "participation_form": ParticipationForm(),
        "search_form": search_form,
        "has_any_match": has_any_match,
        "schema_ready": True,
        "categories": categories,
        "total_matches": total_matches,
        "today_matches": today_matches,
        "total_players": total_players,
        "sports_count": sports_count,
        "popular_sports": popular_sports,
        "recent_activity": recent_activity,
        "players_online": players_online,
        "players_active_today": players_active_today,
    }

    return render(request, "matches/dashboard.html", context)


@require_http_methods(["POST"])
@csrf_exempt
def create_match(request: HttpRequest):
    _ensure_default_categories()
    if not _is_schema_ready():
        return JsonResponse(
            {
                "success": False,
                "errors": {
                    "__all__": [
                        "Database belum dimigrasikan. Jalankan python manage.py migrate terlebih dahulu.",
                    ]
                },
            },
            status=503,
        )

    if request.content_type == "application/json":
        data = json.loads(request.body)
        form = MatchForm(data)
    else:
        form = MatchForm(request.POST)

    if form.is_valid():
        match = form.save()
        Participation.objects.create(match=match, user=request.user, message="")
        Group.objects.create(match=match, name=f"Group {match.title}")
        return JsonResponse(
            {
                "success": True,
                "message": "Match baru berhasil dibuat.",
                "match": _serialize_match(match),
            },
            status=201,
        )

    return JsonResponse({"success": False, "errors": form.errors}, status=400)



@require_http_methods(["POST"])
@csrf_exempt
def book_match(request: HttpRequest, match_id: uuid):
    if not _is_schema_ready():
        return JsonResponse(
            {
                "success": False,
                "errors": {
                    "__all__": [
                        "Database belum dimigrasikan. Jalankan python manage.py migrate terlebih dahulu.",
                    ]
                },
            },
            status=503,
        )

    match = get_object_or_404(Match.objects.select_related("category"), pk=match_id)

    if match.available_slots <= 0:
        return JsonResponse(
            {
                "success": False,
                "errors": {
                    "__all__": ["Match ini sudah penuh. Pilih match lain atau buat baru."]
                },
            },
            status=400,
        )

    if Participation.objects.filter(match=match, user=request.user).exists():
        return JsonResponse(
            {
                "success": False,
                "errors": {
                    "__all__": ["Kamu sudah bergabung pada match ini."]
                },
            },
            status=400,
        )

    form = ParticipationForm({"user": request.user.pk, "message": request.POST.get("message", "")})
    if form.is_valid():
        participation: Participation = form.save(commit=False)
        participation.match = match
        participation.save()

        updated_match = Match.objects.select_related("category").get(id=match_id)

        return JsonResponse(
            {
                "success": True,
                "message": "Kamu berhasil mendaftar pada match ini.",
                "match": _serialize_match(updated_match),
            }
        )

    return JsonResponse({"success": False, "errors": form.errors}, status=400)

@csrf_exempt
def delete_match(request: HttpRequest, match_id: uuid = ''):
    if request.user.role != 'admin':
        return HttpResponse(status=401)
    elif match_id:
        get_object_or_404(Match, id=match_id).delete()
    else:
        Match.objects.all().delete()
    return HttpResponse(status=204)

def get_match(request: HttpRequest, match_id: uuid = None):
    if match_id:
        match = get_object_or_404(Match, id=match_id)
        data = serializers.serialize("json", [match])
    else:
        matches = Match.objects.all()
        data = serializers.serialize("json", matches)
    return JsonResponse({"data": json.loads(data)})

    