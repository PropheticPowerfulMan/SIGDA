# SIGDA

Système intégré de gestion documentaire des agents. Projet proposé pour le Secrétariat Général auprès du Président de la République démocratique du Congo.

**Fondateur, concepteur et propriétaire déclaré du projet SIGDA** — LOKALA LOMBOTO JONATHAN.

## Indépendance du projet

SIGDA et SSDC sont deux projets indépendants, avec leurs propres dépôts, applications et données. [SSDC](https://github.com/PropheticPowerfulMan/ssdc/blob/main/README.md) a servi de référence pour la présentation de la démonstration. L’atelier SIGDA fonctionne avec son propre code et son propre catalogue fictif.

## Démonstration GitHub Pages

### Produire un document avec les données d’un agent

L’ouverture du site affiche la connexion, y compris lorsqu’une session précédente existe. Après connexion, utilisez **Créer un document**.

1. **Modèle** — choisissez le type de document et le style du texte.
2. **Données** — sélectionnez un dossier dans la base agents. Pour un nouvel agent, renseignez le nom, le matricule, le service, la fonction et le grade, puis cliquez sur **Enregistrer le dossier agent**. Les données sélectionnées deviennent la source du document.
3. **Détails** — complétez les champs propres au modèle. Une convocation demande le rendez-vous et son motif ; une mission demande ses dates, son lieu et son objet ; un bordereau demande les pièces, leur nombre et le destinataire.
4. **Vérification** — relisez les données et le document rempli, puis enregistrez le brouillon et ouvrez **Mes tâches**. Attribuez le contrôle à SECAD. Le document sera imprimable après SECAD → AP → DIRCAB. Le dialogue d’impression permet aussi de choisir « Enregistrer en PDF ».

La démonstration conserve une base agents **IndexedDB locale au navigateur**, initialisée avec deux dossiers fictifs. Les dossiers ajoutés ou modifiés restent disponibles après rechargement sur cet appareil. Ils ne sont pas envoyés à un serveur ni partagés entre appareils. Utilisez des données fictives sur GitHub Pages. Les documents personnalisés y sont composés pour l’impression dans le navigateur ; les 66 exemples du catalogue sont des images avec filigrane « APERÇU — NON VALIDÉ », sans PDF public préémis. La composition imprimée utilise Times New Roman lorsque cette police est installée sur l’appareil, sinon la famille sérif du navigateur. Le moteur serveur incorpore la véritable Times New Roman dans les PDF.

Dans Django, **AgentRecord** conserve les dossiers dans SQLite, avec un matricule unique par compte et contrôle des accès. Le générateur relit le dossier en base. L’enregistrement conserve les données, le texte et une empreinte de la révision. Les aperçus ne livrent aucun PDF imprimable. Chaque tâche est nominative, possède un profil, un cycle et une révision, et peut recevoir une échéance. Le contrôle SECAD, le visa AP et la décision DIRCAB doivent porter sur la même version. Un retour motivé remet le dossier à OPS et impose un nouveau circuit. La validation finale archive les octets du PDF et leur SHA-256 ; les ouvertures ultérieures vérifient cette empreinte et ne régénèrent pas le fichier. Chaque ouverture est journalisée.

Les modèles concernant une pièce ou un service ne demandent pas d’agent : ils utilisent les coordonnées du service émetteur et les champs du document. Le catalogue historique reste un espace d’exemples, avec un accès explicite au parcours de création.

Le QR de la composition navigateur est généré localement avec [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator/tree/83b7e8fe3fddd3b0368dbafd6ce56995bd25e3c8), dont la licence MIT accompagne les sources.

La démonstration publique propose quatre comptes fictifs, tous avec le mot de passe `SIGDA-demo-2026!` :

| Identifiant | Responsabilité |
| --- | --- |
| `ops` (ou `demo`) | Base agents, saisie, correction et attribution du contrôle à SECAD. |
| `secad` | Contrôle administratif ; transmission à AP ou retour motivé à OPS. |
| `ap` | Visa hiérarchique ; transmission à DIRCAB ou retour motivé à OPS. |
| `dircab` | Validation finale autorisant l’impression, retour ou refus final, pilotage global. |

Pour tester le circuit, restez dans le même navigateur et changez de compte à chaque étape. Les données fictives et l’historique de cette simulation sont conservés dans IndexedDB sur cet appareil. La connexion simulée et les contrôles JavaScript ne constituent pas une protection de données ; les habilitations réelles sont vérifiées côté Django. GitHub Pages ne contient aucune donnée institutionnelle réelle.

**Mes tâches** présente les documents du périmètre du compte et leurs responsables nominatifs. **Activité et traçabilité** est réservé à DIRCAB. Le tableau affiche les courbes quotidiennes, la charge par étape et les retards, la distribution des délais (Q1, médiane, Q3, P90), le taux d’approbation et son intervalle de Wilson à 95 %, les utilisateurs distincts et le journal des actions. Les chiffres sont calculés à partir des événements enregistrés, sans activité historique inventée. Les périodes couvrent 7, 30 ou 90 jours calendaires à Kinshasa. Chaque graphique dispose d’un tableau de valeurs et d’une méthode explicite. Les autres profils conservent l’historique de leurs documents et tâches. Une ouverture de PDF ou du dialogue d’impression ne prouve pas une impression physique.

**Assistant** propose un guidage local fondé sur le catalogue et les procédures. Il suggère des modèles et ouvre les écrans concernés. Ce mode fonctionne sans modèle génératif. L’interface reprend la direction visuelle de SSDC avec un menu bleu nuit et des accents dorés. La police Manrope est hébergée localement, avec des textes agrandis et une hiérarchie plus aérée. Le thème Soleil associe des surfaces ivoire atténuées, des contours sable et des accents dorés. Les barres de défilement reprennent les couleurs de chaque surface, y compris dans le catalogue, le menu sombre et l’aperçu. L’aperçu du papier est adouci à l’écran et l’impression utilise le rendu d’origine.

### Connexion de l’assistant à GPT

Dans Django, définissez `OPENAI_API_KEY` dans l’environnement du serveur puis redémarrez-le. Le mode GPT devient sélectionnable sur la page Assistant. Le modèle par défaut est `gpt-5.4-mini`, configurable avec `SIGDA_OPENAI_MODEL`.

L’application utilise l’API Responses avec `store=false`. L’Assistant envoie la question saisie et le descriptif public des modèles. L’atelier envoie uniquement le corps du texte soumis pour reformulation et ses consignes de préservation des faits. Chaque appel est indépendant. Le formulaire Assistant accepte 2 000 caractères, l’éditeur documentaire 1 800. La sortie est limitée à 1 200 tokens et les deux écrans partagent dix appels GPT par minute et par compte. Le compteur utilise le cache Django, local au processus par défaut. Un déploiement multi-processus doit configurer un cache partagé pour appliquer cette limite globalement.

Le guidage local est disponible dans la démonstration GitHub Pages. Le mode GPT requiert le serveur Django et une clé API utilisable. La connexion réelle à OpenAI doit être testée après configuration de cette clé. Les tests automatisés vérifient le contrat de l’API avec des réponses simulées. [API Responses](https://developers.openai.com/api/reference/resources/responses/methods/create), [modèle configurable](https://developers.openai.com/api/docs/models/gpt-5.4-mini).

Après la décision finale DIRCAB, la version validée peut être imprimée seule sur une feuille A4. Dans Django, ouvrez le PDF final conservé ; dans la simulation publique, ouvrez le document validé puis **Imprimer la version validée**. Les exemples et les aperçus restent non validés. Tous les documents de démonstration conservent la mention SPÉCIMEN — NON VALABLE.

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

Dans **Rédaction et reformulation**, changez la variante locale ou modifiez le corps du texte. Si GPT est configuré, il peut proposer une nouvelle formulation. Les identités et chiffres présents dans la rédaction initiale sont contrôlés. Relisez les faits et le sens, puis utilisez **Appliquer à l’aperçu** pour examiner cet exemple non validé. Le gabarit institutionnel reste fixe. La rédaction personnalisée n’est pas encore enregistrée dans le circuit des demandes et reste dans la page ouverte.

L’image de l’emblème fournie par le porteur du projet est utilisée dans l’atelier et les PDF. L’usage institutionnel de l’identité visuelle relève de l’autorisation de l’institution.

### Démarrage sous Windows

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r apps/backend/requirements.txt
.venv/Scripts/python apps/backend/manage.py migrate
$env:SIGDA_DEMO_PASSWORD = "Choisissez-un-mot-de-passe-local"
.venv/Scripts/python apps/backend/manage.py create_workflow_demo_users
.venv/Scripts/python apps/backend/manage.py runserver 127.0.0.1:8000 --insecure
```

Ouvrir [l’atelier local](http://127.0.0.1:8000/) et utiliser `ops`, `secad`, `ap` ou `dircab` avec le mot de passe local choisi. La commande ne remplace pas les mots de passe de comptes existants. Le serveur est prévu pour une exécution locale avec données fictives. `--insecure` distribue les ressources du serveur de développement avec `DEBUG=False`. Les installations existantes doivent exécuter `migrate` : les anciennes demandes sans copie des données restent consultables, mais un nouveau document doit être préparé pour suivre le circuit complet.

### Vérification

```powershell
.venv/Scripts/python apps/backend/manage.py check
.venv/Scripts/python apps/backend/manage.py test sigda
node scripts/test_statistics.cjs
```

## Périmètre

- `apps/backend/sigda/catalog.py` contient le catalogue de démonstration.
- `apps/backend/sigda/pdf.py` compose les PDF avec ReportLab.
- L’atelier utilise des gabarits HTML Django. Le catalogue d’exemples est en mémoire ; les dossiers du parcours guidé sont conservés en base. Les références de spécimen sont reproductibles par agent, modèle et année.
- Le projet cible prévoit une interface React, PostgreSQL, une API DRF, l’identité institutionnelle, les habilitations à l’échelle de l’administration, la signature électronique et l’archivage institutionnel, les exports DOCX et l’authenticité. Ces éléments restent à livrer, ainsi que les PDF de présentation et le manuel illustré.
- Voir [l’architecture de SIGDA](docs/architecture.md) pour le périmètre livré, le modèle de données cible et les invariants de réception.
