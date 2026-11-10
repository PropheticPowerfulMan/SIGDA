"""Assemble the public Pages demo from its static sources and fictitious catalogue."""

import re
import sys
from datetime import date
from hashlib import sha256
from itertools import product
from json import dumps
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "apps" / "demo"
DIST = ROOT / "dist"
OUTPUT = DIST / "demo"
STATIC_FILES = (
    "index.html", "login.html", "app.css", "login.css",
    "app.js", "theme.js", "demo-auth.js", "menu.js",
    "manifest.webmanifest", "sw.js", "pwa.js", "offline.html",
    "print.css", "print.js",
    "requests.js",
)
ICONS = ("icon-192.png", "icon-512.png", "apple-touch-icon.png")
SPECIMEN_DATE = date(2026, 1, 15)
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

sys.path.insert(0, str(ROOT / "apps" / "backend"))

from sigda.catalog import AGENTS, DOCUMENT_TYPES, format_date
from sigda.pdf import EMBLEM, render_pdf
from sigda.preview import render_preview


def validate_output(files: set[Path]) -> None:
    """Reject extra files and filesystem redirects before publishing the build."""
    directories = {Path("."), Path("assets"), Path("assets/specimens"), Path("assets/icons")}
    for directory in (DIST, *(OUTPUT / relative for relative in sorted(directories))):
        if directory.is_symlink() or directory.resolve() != directory:
            raise ValueError(f"Chemin de sortie redirigé : {directory}")
        if directory.exists() and not directory.is_dir():
            raise ValueError(f"Le chemin de sortie n’est pas un dossier : {directory}")
        if directory == DIST or not directory.exists():
            continue
        for item in directory.iterdir():
            relative = item.relative_to(OUTPUT)
            if item.is_symlink() or relative not in files | directories:
                raise ValueError(f"Élément inattendu dans la sortie : {item}")
            if relative in files and not item.is_file():
                raise ValueError(f"Le fichier de sortie attendu n’est pas un fichier : {item}")


def build_demo() -> None:
    if any(not SLUG.fullmatch(key) for key in (*DOCUMENT_TYPES, *AGENTS)):
        raise ValueError("Les identifiants du catalogue doivent être des slugs ASCII.")

    specimens = {
        Path("assets/specimens") / f"{kind}-{agent}.pdf": (kind, agent)
        for kind, agent in product(DOCUMENT_TYPES, AGENTS)
    }
    if len(specimens) != len(DOCUMENT_TYPES) * len(AGENTS):
        raise ValueError("Deux spécimens partagent le même nom de fichier.")

    sources = {Path(name): DEMO / name for name in STATIC_FILES}
    sources[Path("assets/EmblemRDC.jpg")] = EMBLEM
    for name in ICONS:
        sources[Path("assets/icons") / name] = EMBLEM.parent / "icons" / name
    for source in sources.values():
        if source.resolve() != source or not source.is_file():
            raise ValueError(f"Ressource absente ou redirigée : {source}")

    public_agents = {
        key: {"name": agent.name, "registration": agent.registration, "service": agent.service}
        for key, agent in AGENTS.items()
    }
    public_documents = {
        key: {"title": kind.title, "description": kind.description, "category": kind.category}
        for key, kind in DOCUMENT_TYPES.items()
    }
    catalogue = f"const agents = {dumps(public_agents)};\nconst documents = {dumps(public_documents)};\n"
    digest = sha256(catalogue.encode("utf-8"))
    for relative, source in sorted(sources.items()):
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(source.read_bytes())
    revision = digest.hexdigest()[:12]

    previews = {path.with_suffix(".png") for path in specimens}
    files = {*sources, *specimens, *previews, Path("catalogue.js"), Path(".nojekyll")}
    validate_output(files)
    DIST.mkdir(exist_ok=True)

    with TemporaryDirectory(prefix="sigda-demo-", dir=DIST) as temp:
        staging = Path(temp) / "site"
        (staging / "assets" / "specimens").mkdir(parents=True)
        (staging / "catalogue.js").write_text(catalogue, encoding="utf-8")
        for relative, source in sources.items():
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if relative.name in {"index.html", "login.html"}:
                html = source.read_text(encoding="utf-8")
                html = re.sub(r'((?:src|href)="\./[a-z-]+\.(?:css|js))"', rf'\1?v={revision}"', html)
                target.write_text(html, encoding="utf-8")
            else:
                copyfile(source, target)

        date_label = format_date(SPECIMEN_DATE)
        for relative, (kind, agent_key) in specimens.items():
            document = DOCUMENT_TYPES[kind]
            agent = AGENTS[agent_key]
            reference = f"SPEC-{document.prefix}-{agent.registration}-{SPECIMEN_DATE.year}"
            pdf = render_pdf(kind, document, agent, reference, date_label)
            (staging / relative).write_bytes(pdf)
            (staging / relative.with_suffix(".png")).write_bytes(render_preview(pdf))
        (staging / ".nojekyll").touch()

        validate_output(files)
        if not OUTPUT.exists():
            staging.rename(OUTPUT)
        else:
            for relative in sorted(files):
                destination = OUTPUT / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                (staging / relative).replace(destination)


if __name__ == "__main__":
    try:
        build_demo()
    except (OSError, ValueError) as error:
        raise SystemExit(f"Impossible de construire la démonstration. {error}") from error
    print(f"Démonstration prête dans {OUTPUT.relative_to(ROOT)}.")
