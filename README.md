# SIGDA

Système intégré de gestion documentaire des agents. Projet proposé pour le Secrétariat Général auprès du Président de la République démocratique du Congo.

**Fondateur, concepteur et propriétaire déclaré du projet SIGDA** — LOKALA LOMBOTO JONATHAN.

## Indépendance du projet

SIGDA et SSDC sont deux projets indépendants, avec leurs propres dépôts, applications et données. [SSDC](https://github.com/PropheticPowerfulMan/ssdc/blob/main/README.md) a servi de référence pour la présentation de la démonstration. L’atelier SIGDA fonctionne avec son propre code et son propre catalogue fictif.

## Démonstration GitHub Pages

La démonstration publique simule une connexion avec l’identifiant `demo` et le mot de passe `SIGDA-demo-2026!`. Elle permet d’explorer deux dossiers fictifs, de choisir un modèle documentaire et de télécharger le PDF A4 correspondant. Le site statique dispose de quatre spécimens générés par le même moteur que l’atelier Django.

La connexion simulée ne protège aucune donnée. GitHub Pages sert uniquement des ressources de démonstration publiques. L’application Django utilise ses propres comptes et vérifie les accès au serveur.

Le menu ouvre cinq vues distinctes. Sur GitHub Pages, **Demandes** permet de créer puis de traiter un brouillon fictif. **Activité** calcule les indicateurs de cette simulation et affiche ses actions horodatées. Le journal de démonstration reste dans l’onglet du navigateur.

Dans les deux ateliers, **Imprimer** ouvre le dialogue d’impression avec le spécimen seul sur une feuille A4. Le PDF original peut aussi être ouvert et imprimé dans un lecteur PDF.

Le bouton **Installer SIGDA** ouvre l’installation du navigateur lorsqu’elle est disponible et propose les étapes manuelles sur les autres appareils. L’application installée affiche une icône qui associe l’emblème au sigle SIGDA. La démonstration et l’atelier local ont chacun leur propre identifiant d’installation. L’installation depuis l’application locale nécessite un contexte sécurisé comme `http://127.0.0.1`. Hors connexion, la PWA affiche une page de reprise. Le service worker ne met en cache ni les dossiers, ni les PDF, ni les réponses de connexion.

### Construire et prévisualiser

```powershell
python -m pip install "reportlab>=4.4,<5" "pypdfium2>=5.13,<6"
python scripts/build_demo.py
python -m http.server 8080 --bind 127.0.0.1 --directory dist/demo
```

Ouvrir [la prévisualisation locale](http://127.0.0.1:8080/). Le dossier `dist/demo` est le seul contenu de l’artefact Pages. Il contient l’interface statique, l’emblème fourni et les quatre PDF fictifs avec leurs aperçus.

Le workflow [Démonstration GitHub Pages](.github/workflows/pages.yml) construit et publie cet artefact depuis `main`. Dans le dépôt SIGDA, choisir **GitHub Actions** comme source dans **Settings → Pages** pour activer la publication. L’adresse cible est [propheticpowerfulman.github.io/SIGDA](https://propheticpowerfulman.github.io/SIGDA/).

## Atelier documentaire local

Sélectionnez l’un des deux dossiers fictifs et un modèle. L’aperçu et le téléchargement utilisent le même moteur PDF A4. Les deux modèles reprennent la structure de l’attestation de travail de nuit et de la notification de régularisation fournies. Les textes, les identités et les matricules sont des exemples. Les PDF portent la mention « SPÉCIMEN — NON VALABLE », un préfixe de référence `SPEC-` et une zone de signature et de cachet vierge.

L’image de l’emblème fournie par le porteur du projet est utilisée dans l’atelier et les PDF. L’usage institutionnel de l’identité visuelle relève de l’autorisation de l’institution.

### Démarrage sous Windows

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r apps/backend/requirements.txt
.venv/Scripts/python apps/backend/manage.py migrate
.venv/Scripts/python apps/backend/manage.py create_demo_user
.venv/Scripts/python apps/backend/manage.py create_demo_user --reviewer
.venv/Scripts/python apps/backend/manage.py runserver 127.0.0.1:8000 --insecure
```

Ouvrir [l’atelier local](http://127.0.0.1:8000/), puis saisir `demo` et le mot de passe choisi lors de la création du compte. Django protège le tableau de bord, les aperçus et les PDF avec une session. Le serveur est prévu pour une exécution locale avec données fictives. L’option `--insecure` permet au serveur Django de développement de distribuer le CSS et l’emblème avec `DEBUG=False`.

Dans **Demandes**, créez un brouillon avec `demo` et soumettez-le. Connectez-vous avec `demo-valideur` et le mot de passe choisi pour ce compte afin d’approuver ou de refuser la demande. Un refus exige un motif. Chaque étape conserve l’auteur, la date et le commentaire éventuel. Même approuvé, le PDF reste un spécimen. Les installations locales existantes doivent exécuter `migrate` avant d’utiliser ce parcours.

**Activité** agrège ce journal sur 7, 30 ou 90 jours calendaires dans le fuseau de Kinshasa. Le taux d’approbation est le rapport entre les approbations et toutes les décisions de la période. La médiane et le P90 mesurent le délai entre soumission et décision, même si la soumission est antérieure à la période. Le tableau indique l’effectif mesuré et distingue le stock actuel des événements sur la période. Chaque compte voit uniquement les demandes auxquelles il a accès.

### Vérification

```powershell
.venv/Scripts/python apps/backend/manage.py check
.venv/Scripts/python apps/backend/manage.py test sigda
```

## Périmètre

- `apps/backend/sigda/catalog.py` contient le catalogue de démonstration.
- `apps/backend/sigda/pdf.py` compose les PDF avec ReportLab.
- L’atelier utilise des gabarits HTML Django. Les agents et les modèles sont en mémoire. Les références de spécimen sont reproductibles par agent, modèle et année.
- Le projet cible prévoit une interface React, PostgreSQL, une API DRF, l’identité institutionnelle, les habilitations, les workflows, l’archivage, les exports DOCX et l’authenticité. Ces éléments restent à livrer, ainsi que les PDF de présentation et le manuel illustré.
- Voir [l’architecture de SIGDA](docs/architecture.md) pour le périmètre livré, le modèle de données cible et les invariants de réception.

