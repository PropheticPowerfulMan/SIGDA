from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.templatetags.static import static
from django.views.decorators.http import require_safe


_PWA_ASSETS = settings.BASE_DIR.parent / "demo"


@require_safe
def manifest(request):
    return JsonResponse(
        {
            "id": "/sigda-gestion-documentaire",
            "name": "SIGDA · Gestion documentaire des agents",
            "short_name": "SIGDA",
            "description": "Atelier de consultation des dossiers agents et de préparation de spécimens administratifs.",
            "lang": "fr",
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "background_color": "#0a0f1d",
            "theme_color": "#0a0f1d",
            "icons": [
                {
                    "src": static(f"sigda/icons/icon-{size}.png"),
                    "sizes": f"{size}x{size}",
                    "type": "image/png",
                }
                for size in (192, 512)
            ],
        },
        content_type="application/manifest+json",
    )


@require_safe
def service_worker(request):
    return FileResponse(
        (_PWA_ASSETS / "sw.js").open("rb"),
        content_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )


@require_safe
def offline(request):
    return FileResponse(
        (_PWA_ASSETS / "offline.html").open("rb"),
        content_type="text/html; charset=utf-8",
    )
