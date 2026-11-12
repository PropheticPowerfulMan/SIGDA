# SIGDA

Système intégré de gestion documentaire des agents. Application destinée au Cabinet du Président de la République démocratique du Congo.

**Fondateur, concepteur et propriétaire déclaré du projet SIGDA** — LOKALA LOMBOTO JONATHAN.

## Indépendance du projet

SIGDA et SSDC sont deux projets indépendants, avec leurs propres dépôts, applications et données. [SSDC](https://github.com/PropheticPowerfulMan/ssdc/blob/main/README.md) a servi de référence pour la présentation de la démonstration. L’atelier SIGDA fonctionne avec son propre code et son propre catalogue fictif.

## Démonstration GitHub Pages

### Produire un document avec les données d’un agent

L’ouverture du site affiche la connexion, y compris lorsqu’une session précédente existe. Après connexion, utilisez **Créer un document**.

1. **Modèle** — choisissez le type de document et le style du texte.
2. **Données** — sélectionnez un dossier dans la base agents. Pour un ajout ou une correction, ouvrez **Maintenance et assistance**. Les profils opérationnels ne modifient pas directement la base. Les données sélectionnées deviennent la source du document.
3. **Détails** — complétez les champs propres au modèle. Une convocation demande le rendez-vous et son motif ; une mission demande ses dates, son lieu et son objet ; un bordereau demande les pièces, leur nombre et le destinataire.
4. **Vérification** — relisez les données et le document rempli, puis enregistrez le brouillon et ouvrez **Mes tâches**. Attribuez le contrôle à SECAD. Le document sera imprimable après SECAD → AP → DIRCAB. Le dialogue d’impression permet aussi de choisir « Enregistrer en PDF ».

La démonstration conserve une base agents **IndexedDB locale au navigateur**, initialisée avec deux dossiers fictifs. Les dossiers ajoutés ou modifiés restent disponibles après rechargement sur cet appareil. Ils ne sont pas envoyés à un serveur ni partagés entre appareils. Utilisez des données fictives sur GitHub Pages. Les documents personnalisés y sont composés pour l’impression dans le navigateur ; les 66 exemples du catalogue sont des images avec filigrane « APERÇU — NON VALIDÉ », sans PDF public préémis. La composition imprimée utilise Times New Roman lorsque cette police est installée sur l’appareil, sinon la famille sérif du navigateur. Le moteur serveur incorpore la véritable Times New Roman dans les PDF.

Dans Django, **AgentRecord** conserve les dossiers dans SQLite, avec un matricule unique par compte et contrôle des accès. Le générateur relit le dossier en base. L’enregistrement conserve les données, le texte et une empreinte de la révision. Les aperçus ne livrent aucun PDF imprimable. Chaque tâche est nominative, possède un profil, un cycle et une révision, et peut recevoir une échéance. Le contrôle SECAD, le visa AP et la décision DIRCAB doivent porter sur la même version. Un retour motivé remet le dossier à OPS et impose un nouveau circuit. La validation finale archive les octets du PDF et leur SHA-256 ; les ouvertures ultérieures vérifient cette empreinte et ne régénèrent pas le fichier. Chaque ouverture est journalisée.

Les modèles concernant une pièce ou un service ne demandent pas d’agent : ils utilisent les coordonnées du service émetteur et les champs du document. Le catalogue historique reste un espace d’exemples, avec un accès explicite au parcours de création.

Le QR de la composition navigateur est généré localement avec [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator/tree/83b7e8fe3fddd3b0368dbafd6ce56995bd25e3c8), dont la licence MIT accompagne les sources.

La démonstration publique propose quatre comptes fictifs, tous avec le mot de passe `SIGDA-demo-2026!` :

| Identifiant | Responsabilité |
| --- | --- |
| `ops` (ou `demo`) | Consultation des agents, préparation et correction des documents, attribution du contrôle à SECAD. |
| `secad` | Contrôle administratif ; transmission à AP ou retour motivé à OPS. |
| `ap` | Visa hiérarchique ; transmission à DIRCAB ou retour motivé à OPS. |
| `dircab` | Validation finale autorisant l’impression, retour ou refus final, pilotage global. |

Pour tester le circuit, restez dans le même navigateur et changez de compte à chaque étape. Les données fictives et l’historique de cette simulation sont conservés dans IndexedDB sur cet appareil. La connexion simulée et les contrôles JavaScript ne constituent pas une protection de données ; les habilitations réelles sont vérifiées côté Django. GitHub Pages ne contient aucune donnée institutionnelle réelle.

**Mes tâches** présente les documents du périmètre du compte et leurs responsables nominatifs. **Activité et traçabilité** est réservé à DIRCAB. Le tableau affiche les courbes quotidiennes, la charge par étape et les retards, la distribution des délais (Q1, médiane, Q3, P90), le taux d’approbation et son intervalle de Wilson à 95 %, les utilisateurs distincts et le journal des actions. Les chiffres sont calculés à partir des événements enregistrés, sans activité historique inventée. Les périodes couvrent 7, 30 ou 90 jours calendaires à Kinshasa. Chaque graphique dispose d’un tableau de valeurs et d’une méthode explicite. Les autres profils conservent l’historique de leurs documents et tâches. Une ouverture de PDF ou du dialogue d’impression ne prouve pas une impression physique.

**Assistant** propose un guidage local fondé sur le catalogue et les procédures. Il suggère des modèles et ouvre les écrans concernés. Ce mode fonctionne sans modèle génératif. L’interface reprend la direction visuelle de SSDC avec un menu bleu nuit et des accents dorés. Le mode typographique « Scientifique », identifié dans EduPay KCS, utilise EB Garamond. SIGDA embarque cette police variable sous licence OFL depuis le dépôt officiel Google Fonts (`ofl/ebgaramond`). Les contrôles mesurent environ 19–20 px et les zones tactiles au moins 44 px. Le corps documentaire reste en Times New Roman. La première ligne de chaque paragraphe commence à la moitié de la largeur utile, ce qui correspond au centre de la page A4 avec les marges symétriques. Le thème Soleil associe des surfaces ivoire atténuées, des contours sable et des accents dorés. Les barres de défilement reprennent les couleurs de chaque surface, y compris dans le catalogue, le menu sombre et l’aperçu. L’aperçu du papier est adouci à l’écran et l’impression utilise le rendu d’origine.

### Connexion de l’assistant à GPT

Dans Django, définissez `OPENAI_API_KEY` dans l’environnement du serveur puis redémarrez-le. Le mode GPT devient sélectionnable sur la page Assistant. Le modèle par défaut est `gpt-5.4-mini`, configurable avec `SIGDA_OPENAI_MODEL`.

L’application utilise l’API Responses avec `store=false`. L’Assistant envoie la question saisie et le descriptif public des modèles. L’atelier envoie uniquement le corps du texte soumis pour reformulation et ses consignes de préservation des faits. Chaque appel est indépendant. Le formulaire Assistant accepte 2 000 caractères, l’éditeur documentaire 1 800. La sortie est limitée à 1 200 tokens et les deux écrans partagent dix appels GPT par minute et par compte. Le compteur utilise le cache Django, local au processus par défaut. Un déploiement multi-processus doit configurer un cache partagé pour appliquer cette limite globalement.

Le guidage local est disponible dans la démonstration GitHub Pages. Le mode GPT requiert le serveur Django et une clé API utilisable. La connexion réelle à OpenAI doit être testée après configuration de cette clé. Les tests automatisés vérifient le contrat de l’API avec des réponses simulées. [API Responses](https://developers.openai.com/api/reference/resources/responses/methods/create), [modèle configurable](https://developers.openai.com/api/docs/models/gpt-5.4-mini).

Après la décision finale DIRCAB, la version validée peut être imprimée seule sur une feuille A4. Dans Django, ouvrez le PDF final conservé ; dans la simulation publique, ouvrez le document validé puis **Imprimer la version validée**. Les exemples et les aperçus restent non validés. Tous les documents de démonstration conservent la mention SPÉCIMEN — NON VALABLE.

Les onze modèles partagent un pied de page sur la largeur utile de la feuille : bande bleue, dorée et rouge, coordonnées sur deux lignes, sept icônes sociales cliquables et QR propre à la version. Les liens Facebook, X/Twitter, Instagram, YouTube, LinkedIn, TikTok et Flickr sont ceux référencés par [le site officiel de la Présidence](https://presidence.cd/) le 12 novembre 2026. Ils sont définis dans `config/institutional_links.json`. Le site, le courriel et les icônes sont des annotations URI dans les PDF. Les coordonnées transcrites du document fourni restent à confirmer avant production.

L’ADN `sigda-dna-v1` associe un UUID stable, une révision et un SHA-256 du contenu et des métadonnées canoniques. La forme courte est imprimée ; le QR encode l’empreinte complète ou renvoie au registre privé. Le SHA-256 des octets du PDF final est conservé séparément à l’archivage. Les corrections créent une nouvelle révision, sans réécrire un PDF déjà validé.

Sur GitHub Pages, le QR ouvre une fiche de lecture des indications déclarées ; aucun registre institutionnel n’est interrogé. Les anciens QR à cinq champs restent lisibles. Sur Django, les QR des dossiers enregistrés renvoient à une vérification après connexion et contrôle du périmètre documentaire. Le serveur compare l’UUID, la révision, le contenu enregistré et le PDF archivé ; les consultations sont journalisées. Une empreinte ou un QR copié ne constitue pas une signature électronique officielle et ne dispense pas de comparer le fichier reçu à l’empreinte du fichier archivé.

Le bouton **Installer SIGDA** ouvre l’installation du navigateur lorsqu’elle est disponible et propose les étapes manuelles sur les autres appareils. L’application installée affiche une icône qui associe l’emblème au sigle SIGDA. La démonstration et l’atelier local ont chacun leur propre identifiant d’installation. L’installation depuis l’application locale nécessite un contexte sécurisé comme `http://127.0.0.1`. Hors connexion, la PWA affiche une page de reprise. Le service worker ne met en cache ni les dossiers, ni les PDF, ni les réponses de connexion.

### Construire et prévisualiser

Le corps des documents utilise la véritable Times New Roman, incorporée en sous-ensemble dans chaque PDF. Sous Windows, SIGDA utilise `C:/Windows/Fonts/times.ttf`. Sur un autre système, définissez `SIGDA_TIMES_NEW_ROMAN` avec le chemin d’une installation autorisée de cette police. Une police absente ou différente provoque un message explicite. Le fichier de police Microsoft n’est pas publié comme ressource web. La compilation Pages utilise un environnement Windows et inclut l’empreinte de la police dans sa révision. Voir les [indications Microsoft sur l’incorporation documentaire](https://learn.microsoft.com/en-us/typography/fonts/font-faq#document-embedding). La licence de Manrope accompagne sa ressource web dans `apps/demo/manrope-license.txt`.

```powershell
python -m pip install "reportlab>=4.4,<5" "pypdfium2>=5.13,<6"
python scripts/build_demo.py
python -m http.server 8080 --bind 127.0.0.1 --directory dist/demo
```

Ouvrir [la prévisualisation locale](http://127.0.0.1:8080/). Le dossier `dist/demo` est le seul contenu de l’artefact Pages. Il contient l’interface statique, l’emblème fourni, 66 aperçus PNG fictifs et le guide PDF de démonstration. Les PDF administratifs finaux restent soumis au workflow.

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
node scripts/test_service_policy.cjs
```

## Périmètre

- `apps/backend/sigda/catalog.py` contient le catalogue de démonstration.
- `apps/backend/sigda/pdf.py` compose les PDF avec ReportLab.
- L’atelier utilise des gabarits HTML Django. Le catalogue d’exemples est en mémoire ; les dossiers du parcours guidé sont conservés en base. Les références de spécimen sont reproductibles par agent, modèle et année.
- Le projet cible prévoit une interface React, PostgreSQL, une API DRF, l’identité institutionnelle, les habilitations à l’échelle de l’administration, la signature électronique et l’archivage institutionnel, les exports DOCX et l’authenticité. Ces éléments restent à livrer, ainsi que les PDF de présentation et le manuel illustré.
- Voir [l’architecture de SIGDA](docs/architecture.md) pour le périmètre livré, le modèle de données cible et les invariants de réception.

## Maintenance, agents et validité annuelle

La période initiale va du **1er janvier au 31 décembre 2027 inclus**. Le 1er janvier 2028 marque l’échéance. Un rappel s’affiche durant les 30 derniers jours. Avant janvier 2027, l’application indique la phase de préparation. Les dates publiques de démonstration sont définies dans `config/deployment.json` ; dans Django, une période enregistrée par la maintenance prend priorité. Le renouvellement couvre une année calendaire, avec ajustement du 29 février au 28 février l’année suivante.

Après expiration, les nouvelles compositions, leurs enregistrements et les nouvelles soumissions OPS sont suspendus. Les demandes déjà soumises peuvent terminer leur circuit. La consultation et l’impression des documents déjà validés restent disponibles, ainsi que les demandes d’assistance. Django vérifie la date du serveur ; la démonstration statique illustre cette règle côté navigateur et ne constitue pas un mécanisme d’habilitation ou de licence inviolable.

L’équipe technique dispose d’un groupe distinct `SIGDA_MAINTENANCE`, réservé à des comptes nominatifs actifs avec statut staff, séparés des quatre groupes opérationnels. Aucun compte ni mot de passe de maintenance n’est publié. Création locale :

```powershell
.venv/Scripts/python apps/backend/manage.py create_maintenance_user votre-identifiant-nominatif
```

Le mot de passe est demandé de façon masquée, ou peut provenir de `SIGDA_MAINTENANCE_PASSWORD`. La commande refuse de réhabiliter ou de modifier un compte existant. Après connexion, **Administration technique** permet le traitement des demandes, le renouvellement motivé et l’import CSV d’agents pour un compte OPS. En-tête : `name,registration,service,job,grade`. Le fichier UTF-8 est limité à 1 Mo et 1 000 lignes. Toutes les lignes sont validées avant la transaction ; les matricules existants sont actualisés, aucun agent n’est supprimé. Les imports, périodes et suivis sont journalisés avec l’auteur et l’heure.

Dans Django, **Maintenance et assistance** conserve la demande dans la file de traitement de l’équipe habilitée. Sur GitHub Pages, le formulaire prépare un fichier texte à transmettre et conserve sa copie sur cet appareil ; il ne prétend pas envoyer la demande à un serveur. Les mises à jour du logiciel restent effectuées par les responsables du dépôt et du déploiement.

## Mobile et identité PWA

Le menu devient un panneau latéral sur téléphone et tablette étroite, avec fermeture tactile, touche Échap et confinement du focus. Les formulaires restent sur une colonne, les dossiers agents deviennent des cartes et les graphiques gardent leurs tableaux de valeurs. Les tableaux scientifiques défilent dans leur propre cadre. Le mot de passe peut être affiché ou masqué et redevient masqué à la soumission ou lorsque la page perd sa visibilité.

La PWA possède une icône reprenant l’emblème fourni de la RDC et le nom **SIGDA**, une variante maskable et une icône Apple. Les identifiants existants sont conservés pour mettre à jour les installations sans créer de doublons : `/sigda-gestion-documentaire-demo` sur Pages et `/sigda-gestion-documentaire` côté Django. Ces identifiants, le périmètre `/SIGDA/` sur Pages et les caches `sigda-offline` sont réservés à SIGDA et ne doivent pas être repris pour une autre application de la Présidence.

Sur Windows, Linux et Android, l’installation est proposée par les navigateurs compatibles, notamment Chrome ou Edge. Sur iPhone/iPad, Safari utilise Partager → Sur l’écran d’accueil. Sur macOS, Safari propose Ajouter au Dock quand cette fonction est disponible. La présence d’un bouton d’installation dépend du système et du navigateur ; le site reste accessible dans le navigateur. Le service worker conserve une page de reprise hors connexion et ne met pas les documents privés en cache.

## Retours d’action et animations

Les confirmations et les échecs apparaissent dans une fenêtre centrée, avec résultat explicite, bouton de continuation, focus clavier et fermeture par Échap. Les demandes, transitions, aperçus, reformulations et opérations de maintenance s’appuient sur le résultat réellement enregistré. Les téléchargements sont annoncés comme préparés ou lancés ; aucune impression physique n’est affirmée. Les champs incomplets sont signalés avant envoi. Les effets de clic, transitions et indicateurs de traitement suivent `prefers-reduced-motion`. La barre de progression est indéterminée : elle accompagne un traitement réel sans inventer un pourcentage d’avancement.

Un indicateur discret nomme l’opération en cours (connexion, ouverture de page, préparation d’aperçu ou enregistrement). Les boutons concernés signalent leur état occupé aux lecteurs d’écran. Les opérations très courtes n’imposent aucun délai artificiel ; le retour depuis le cache de navigation réinitialise les indicateurs.

À l’étape de vérification, **Aperçu grand format** ouvre une liseuse consacrée au document rempli. Elle propose un zoom de 20 à 250 %, l’ajustement à la largeur, la page entière et la taille 100 %. Sur mobile, la liseuse occupe l’écran et le document peut défiler dans les deux directions. Échap ferme la liseuse et restitue le focus au bouton d’origine. L’aperçu des dossiers enregistrés côté serveur utilise la même liseuse. Ce mode de lecture ne donne aucun accès supplémentaire au PDF final, réservé aux documents validés.

Sur ordinateur, le menu se réduit progressivement en rail d’icônes et le contenu gagne sa largeur pendant la transition. Sur mobile, les entrées apparaissent successivement dans le panneau coulissant. Le bouton de menu change de forme selon son état. Ces effets sont désactivés avec la préférence système de réduction des animations.

Les nouvelles compositions portent également un emblème en filigrane dans la zone d’écriture, à une opacité de 4,5 %. Le texte reste opaque et l’emblème d’en-tête conserve son rendu normal. Les fichiers déjà validés restent archivés dans leur version originale.

## Tableaux de bord et services d’affectation

OPS, SECAD, AP et DIRCAB ont chacun un tableau de bord avec leurs tâches nominatives et indicateurs adaptés. Le tableau OPS suit ses documents ; SECAD suit ses contrôles ; AP suit ses visas ; DIRCAB suit ses décisions et conserve l’accès au pilotage global. Les données côté serveur sont filtrées par utilisateur, les statistiques globales restant réservées à DIRCAB et à la maintenance habilitée.

Les services sont définis dans `config/services.json`. La composition les présente comme une liste déroulante en lecture seule, alimentée par le dossier agent. Les ajouts et corrections restent réservés à la maintenance ; l’import refuse les services absents de cette liste de démonstration, qui doit être adaptée à l’organigramme validé du Cabinet.

Le menu est fermé dans le HTML dès le premier affichage mobile, se ferme au retour de navigation et utilise des transitions dans les deux sens. Les contrôles de fermeture et de visibilité du mot de passe sont des icônes avec libellés accessibles. Les raccourcis mobiles donnent accès au tableau de bord, à la création ou aux tâches, au pilotage ou à l’assistant, et au menu. La taille de base est ajustée à 18 px sur ordinateur et 17 px sur mobile, avec des cibles tactiles d’au moins 44 px.

Les icônes PWA reprennent désormais l’emblème fourni de la RDC avec un marquage SIGDA distinct. Leurs nouvelles URL contiennent `rdc` afin de faciliter le renouvellement du cache d’icônes. Un raccourci déjà épinglé peut nécessiter d’être recréé si le système conserve l’ancienne image ; l’application ne peut pas forcer la mise à jour du bureau du système.

## Protections serveur et déploiement HTTPS

Les contrôles existants de rôles, d’attribution des tâches, de versions, de CSRF et d’archives restent actifs. Les nouvelles protections incluent une limitation transactionnelle des tentatives de connexion (5 par couple adresse/identifiant et 30 par adresse sur 15 minutes), des cookies HttpOnly/SameSite, une session limitée à 30 minutes d’inactivité, une CSP, l’interdiction d’intégration dans un cadre et l’absence de cache sur les réponses privées. Les compteurs ne conservent ni les mots de passe ni les adresses en clair. Les en-têtes transmis par un client ne servent pas à contourner la limitation d’adresse ; `REMOTE_ADDR` est utilisé.

La configuration locale demeure limitée à localhost. Pour un serveur réel, `sigda.production` exige une clé privée d’au moins 50 caractères et des hôtes explicites, force HTTPS et les cookies sécurisés, et active HSTS pour l’hôte. Le réglage de confiance dans le proxy HTTPS est désactivé par défaut ; il exige `SIGDA_TRUST_HTTPS_PROXY=1` et un proxy contrôlé qui nettoie les en-têtes entrants. Exécutez `manage.py check --deploy --settings=sigda.production` avec vos paramètres privés. HSTS pour tous les sous-domaines et le préchargement doivent être décidés au niveau du domaine, pas activés implicitement.

Ces contrôles ne rendent pas un système inviolable. GitHub Pages reste une démonstration publique à données fictives. Une mise en service institutionnelle exige notamment hébergement administré, MFA/SSO, protection périmétrique, sauvegardes testées, mises à jour, supervision et audit indépendant. Le serveur de développement Django et SQLite ne constituent pas à eux seuls un environnement institutionnel de production. Référence : [liste de déploiement Django](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/).

Le seuil global par adresse peut être adapté avec `SIGDA_LOGIN_IP_LIMIT` (30 par défaut). Un réseau partagé ou un proxy doit être pris en compte lors de la recette, sans faire confiance aux en-têtes d’adresse fournis directement par un client. La limitation applicative ne remplace pas celle du proxy et la supervision des attaques distribuées.

## Supervision et réception des demandes

La maintenance possède un tableau de bord distinct. Sur Django, les demandes des quatre profils arrivent dans une file centralisée, filtrable et paginée. Le suivi conserve l’état, la réponse, l’intervenant et un historique ; les formulaires signalent une modification concurrente. Le demandeur retrouve sa réponse dans son espace. Les compteurs sont interrogés toutes les 20 secondes sans effacer la saisie de l’intervenant. Les journaux d’utilisation et d’interventions sont paginés ; le pilotage statistique est accessible à DIRCAB et aux mainteneurs habilités.

Les mainteneurs sont des comptes actifs staff appartenant au seul groupe technique SIGDA_MAINTENANCE. Ils peuvent superviser les métadonnées et les demandes, importer des agents et renouveler la période. Ce rôle ne leur donne pas automatiquement accès au contenu de tous les documents et ne leur permet pas de prendre les décisions du circuit.

La démonstration dispose d’un profil fictif `maintenance`, avec le même mot de passe public `SIGDA-demo-2026!`. Les demandes et réponses y sont simulées dans la base locale du navigateur, avec notification entre onglets de la même origine. Aucun serveur distant ni courriel de réception n’est simulé comme réel. Le compte technique Django nominatif conserve un mot de passe privé distinct ; les identifiants de démonstration ne doivent jamais être réutilisés en production.

Seule la fenêtre de confirmation de connexion réussie a été retirée. La connexion reste journalisée et les erreurs, les confirmations d’enregistrement, les validations, les téléchargements et la déconnexion conservent leurs retours dédiés.

## Guide illustré de démonstration

La page de connexion publique propose le guide, avec vérification SHA-256 avant le lancement du téléchargement. Il décrit OPS, SECAD, AP, DIRCAB et Maintenance, leurs tableaux de bord, les procédures, les erreurs, la traçabilité et les limites d’exploitation. Son sommaire et ses liens sont cliquables. Les captures sont réelles et issues de services locaux isolés utilisant uniquement des dossiers fictifs.

Le PDF distribué est conservé dans `docs/manual/Guide_utilisateur_SIGDA_demo.pdf`, ses sources et captures dans `docs/manual/`, et sa copie livrable dans `output/pdf/`. La compilation Pages le copie sous `guide-utilisateur-sigda-demo.pdf`. Le guide est volontairement extérieur aux répertoires statiques Django : aucun lien ni fichier de ce guide n’est ajouté à la connexion institutionnelle. Voir [la procédure de régénération](docs/manual/README.md).
