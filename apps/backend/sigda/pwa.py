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
            "name": "SIGDA Cabinet",
            "short_name": "SIGDA",
            "description": "Atelier de consultation des dossiers agents et de préparation de spécimens administratifs.",
            "lang": "fr",
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "display_override": ["standalone", "minimal-ui"],
            "orientation": "any",
            "background_color": "#0a0f1d",
            "theme_color": "#0a0f1d",
            "icons": [
                {
                    "src": static(f"sigda/icons/icon-{size}-rdc.png"),
                    "sizes": f"{size}x{size}",
                    "type": "image/png",
                }
                for size in (192, 512)
            ] + [{"src": static("sigda/icons/maskable-rdc-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "maskable"}],
        },
        content_type="application/manifest+json",
        headers={"Cache-Control":"no-cache"},
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
