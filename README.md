# SIGDA

Système intégré de gestion documentaire des agents. Projet proposé pour le Secrétariat Général auprès du Président de la République démocratique du Congo.

**Fondateur, concepteur et propriétaire déclaré du projet SIGDA** — LOKALA LOMBOTO JONATHAN.

## Indépendance du projet

SIGDA et SSDC sont deux projets indépendants, avec leurs propres dépôts, applications et données. [SSDC](https://github.com/PropheticPowerfulMan/ssdc/blob/main/README.md) a servi de référence pour la présentation de la démonstration. L’atelier SIGDA fonctionne avec son propre code et son propre catalogue fictif.

## Démonstration GitHub Pages

La démonstration publique simule une connexion avec l’identifiant `demo` et le mot de passe `SIGDA-demo-2026!`. Deux dossiers fictifs et onze modèles donnent accès à 22 combinaisons de spécimens A4, chacune proposée en trois styles rédactionnels, soit 66 versions PDF. Le moteur est partagé avec l’atelier Django. Le catalogue se filtre par famille et l’atelier permet de reprendre le dossier et le modèle dans une demande.

La connexion simulée ne protège aucune donnée. GitHub Pages sert uniquement des ressources de démonstration publiques. L’application Django utilise ses propres comptes et vérifie les accès au serveur.

Le menu ouvre six vues distinctes. Sur GitHub Pages, **Demandes** permet de créer puis de traiter un brouillon fictif. **Activité** calcule les indicateurs de cette simulation et affiche ses actions horodatées. Le journal de démonstration reste dans l’onglet du navigateur.

**Assistant** propose un guidage local fondé sur le catalogue et les procédures. Il suggère des modèles et ouvre les écrans concernés. Ce mode fonctionne sans modèle génératif. L’interface reprend la direction visuelle de SSDC avec un menu bleu nuit et des accents dorés. La police Manrope est hébergée localement, avec des textes agrandis et une hiérarchie plus aérée. Le thème Soleil associe des surfaces ivoire atténuées, des contours sable et des accents dorés. Les barres de défilement reprennent les couleurs de chaque surface, y compris dans le catalogue, le menu sombre et l’aperçu. L’aperçu du papier est adouci à l’écran et l’impression utilise le rendu d’origine.

### Connexion de l’assistant à GPT

Dans Django, définissez `OPENAI_API_KEY` dans l’environnement du serveur puis redémarrez-le. Le mode GPT devient sélectionnable sur la page Assistant. Le modèle par défaut est `gpt-5.4-mini`, configurable avec `SIGDA_OPENAI_MODEL`.

L’application utilise l’API Responses avec `store=false`. L’Assistant envoie la question saisie et le descriptif public des modèles. L’atelier envoie uniquement le corps du texte soumis pour reformulation et ses consignes de préservation des faits. Chaque appel est indépendant. Le formulaire Assistant accepte 2 000 caractères, l’éditeur documentaire 1 800. La sortie est limitée à 1 200 tokens et les deux écrans partagent dix appels GPT par minute et par compte. Le compteur utilise le cache Django, local au processus par défaut. Un déploiement multi-processus doit configurer un cache partagé pour appliquer cette limite globalement.

Le guidage local est disponible dans la démonstration GitHub Pages. Le mode GPT requiert le serveur Django et une clé API utilisable. La connexion réelle à OpenAI doit être testée après configuration de cette clé. Les tests automatisés vérifient le contrat de l’API avec des réponses simulées. [API Responses](https://developers.openai.com/api/reference/resources/responses/methods/create), [modèle configurable](https://developers.openai.com/api/docs/models/gpt-5.4-mini).

Dans les deux ateliers, **Imprimer** ouvre le dialogue d’impression avec le spécimen seul sur une feuille A4. Le PDF original peut aussi être ouvert et imprimé dans un lecteur PDF.

Les onze modèles utilisent un pied de page inspiré de l’attestation de service fournie le 11 novembre 2026. Il reprend la bande bleue, dorée et rouge ainsi que la disposition des coordonnées sur deux lignes. Les coordonnées sont transcrites de cet exemple, sans vérification de leur actualité. Le QR à droite ouvre une fiche publique lisible sur mobile, sans connexion. Il fonctionne aussi comme lien cliquable dans le PDF.

La fiche affiche les indications déclarées dans le QR, dont la référence, le modèle, la date, le style et l’empreinte SHA-256 du corps du texte. L’empreinte suit la rédaction effectivement appliquée, y compris un texte personnalisé. Les retours de ligne sont normalisés en LF dans l’éditeur. Le corps du texte et les noms ne figurent pas dans le QR ; ses champs sont dans le fragment de l’URL, lu localement par la page. Cette fiche n’est pas comparée à un registre d’émission et n’authentifie pas le document. L’URL de démonstration est définie dans `apps/backend/sigda/document_qr.py`.

Le bouton **Installer SIGDA** ouvre l’installation du navigateur lorsqu’elle est disponible et propose les étapes manuelles sur les autres appareils. L’application installée affiche une icône qui associe l’emblème au sigle SIGDA. La démonstration et l’atelier local ont chacun leur propre identifiant d’installation. L’installation depuis l’application locale nécessite un contexte sécurisé comme `http://127.0.0.1`. Hors connexion, la PWA affiche une page de reprise. Le service worker ne met en cache ni les dossiers, ni les PDF, ni les réponses de connexion.

### Construire et prévisualiser

Le corps des documents utilise la véritable Times New Roman, incorporée en sous-ensemble dans chaque PDF. Sous Windows, SIGDA utilise `C:/Windows/Fonts/times.ttf`. Sur un autre système, définissez `SIGDA_TIMES_NEW_ROMAN` avec le chemin d’une installation autorisée de cette police. Une police absente ou différente provoque un message explicite. Le fichier de police Microsoft n’est pas publié comme ressource web. La compilation Pages utilise un environnement Windows et inclut l’empreinte de la police dans sa révision. Voir les [indications Microsoft sur l’incorporation documentaire](https://learn.microsoft.com/en-us/typography/fonts/font-faq#document-embedding). La licence de Manrope accompagne sa ressource web dans `apps/demo/manrope-license.txt`.

```powershell
python -m pip install "reportlab>=4.4,<5" "pypdfium2>=5.13,<6"
python scripts/build_demo.py
python -m http.server 8080 --bind 127.0.0.1 --directory dist/demo
```

Ouvrir [la prévisualisation locale](http://127.0.0.1:8080/). Le dossier `dist/demo` est le seul contenu de l’artefact Pages. Il contient l’interface statique, l’emblème fourni et les 66 PDF fictifs avec leurs aperçus.

Le workflow [Démonstration GitHub Pages](.github/workflows/pages.yml) construit et publie cet artefact depuis `main`. Dans le dépôt SIGDA, choisir **GitHub Actions** comme source dans **Settings → Pages** pour activer la publication. L’adresse cible est [propheticpowerfulman.github.io/SIGDA](https://propheticpowerfulman.github.io/SIGDA/).

## Atelier documentaire local

Sélectionnez l’un des deux dossiers fictifs et un modèle. L’aperçu, l’impression et le téléchargement utilisent le même moteur PDF A4. Les gabarits reprennent les structures de l’attestation de travail de nuit et de la notification de régularisation fournies. Le catalogue ajoute des attestations de service, de présence et d’affectation, une convocation, un bordereau, une lettre de transmission, une note de service, une autorisation de sortie et un ordre de mission. Les [repères documentaires](docs/documentary-sources.md) précisent les sources institutionnelles consultées et les limites de cette adaptation. Les PDF portent la mention « SPÉCIMEN — NON VALABLE », un préfixe de référence `SPEC-` et une zone de signature et de cachet vierge.

Dans **Rédaction et reformulation**, changez la variante locale ou modifiez le corps du texte. Si GPT est configuré, il peut proposer une nouvelle formulation. Les identités et chiffres présents dans la rédaction initiale sont contrôlés. Relisez les faits et le sens, puis utilisez **Appliquer à l’aperçu** pour imprimer cette version. Le gabarit institutionnel reste fixe. La rédaction personnalisée n’est pas encore enregistrée dans le circuit des demandes et reste dans la page ouverte.

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
