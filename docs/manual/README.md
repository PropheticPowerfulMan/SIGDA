# Guide utilisateur SIGDA - démonstration

Le guide couvre les quatre profils OPS, SECAD, AP et DIRCAB et l’espace technique Maintenance. Il explique leurs tableaux de bord, la création à partir du dossier agent, les retours, la validation, l’impression, l’ADN numérique, les demandes et les réponses. Un atlas contient les captures complémentaires.

- Texte : `manual_content.json`.
- Captures réelles : `screenshots/`, avec leur origine et leur SHA-256 dans `captures.json`.
- Illustration du pied de page : `illustrations/pied-page.png`, générée à partir du moteur PDF SIGDA.
- Distribution : `Guide_utilisateur_SIGDA_demo.pdf` ; métadonnées et empreintes dans `guide_manifest.json`.
- Livrable local : `output/pdf/Guide_utilisateur_SIGDA_demo.pdf` à la racine du projet.

## Régénération sur Windows

Disposer de l’environnement Python du projet, Chrome, Playwright et des polices Times New Roman et Segoe UI installées sous licence. Le script de capture peut utiliser `SIGDA_PLAYWRIGHT_PATH` et `SIGDA_CHROME` pour adapter les chemins du poste. Il lance uniquement des services locaux fictifs sur les ports 8858 et 8859, avec une base temporaire et un compte technique dont le mot de passe aléatoire n’est ni publié ni affiché.

```powershell
.venv/Scripts/python.exe scripts/build_demo.py
node scripts/capture_manual.cjs
.venv/Scripts/python.exe scripts/build_user_manual.py
.venv/Scripts/python.exe scripts/build_demo.py
```

La première compilation utilise le guide déjà livré et prépare les écrans à capturer. La dernière actualise le PDF distribué et son empreinte de téléchargement. Les captures utilisent un navigateur isolé, sans profil personnel, et ne contactent aucun serveur institutionnel. Les confirmations sont acquittées automatiquement pendant la capture, à l’exception de l’erreur de connexion explicitement illustrée.

Le document comporte une identité d’édition calculée à partir du texte, des captures, de l’illustration, de l’emblème et du script de composition. Son empreinte de fichier PDF est enregistrée séparément. Le PDF ne peut pas contenir sa propre empreinte intégrale sans circularité.

Rendre chaque page avec Poppler et vérifier la mise en page avant redistribution. Contrôler aussi le nombre de pages, les liens, les signets et les captures correspondant à chaque profil. Les services et identifiants figurant dans les images sont fictifs ; aucune signature ni aucun cachet réel n’est reproduit.

## Périmètre de publication

Le guide n’est distribué que dans la démonstration GitHub Pages. Son fichier est extérieur aux répertoires statiques Django. La connexion du serveur privé n’affiche pas ce téléchargement. Une adaptation à la production attend une instruction explicite du porteur du projet.

Le site officiel de la Présidence est la source des liens sociaux. Les coordonnées proviennent du document de référence fourni et doivent être confirmées avant un usage réel. La démarche du guide SSDC a inspiré la présentation pas à pas ; SIGDA et SSDC demeurent indépendants.
