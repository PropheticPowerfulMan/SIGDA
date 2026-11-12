# Historique des versions

## En développement

- Déconnexion sans fenêtre de confirmation ; chargement immédiat du bouton de connexion avec protection contre les doubles clics.
- Réclamations du Cabinet visibles en premier dans Maintenance, recherche par compte, texte ou référence, catégorie Réclamation et guide illustré actualisé avec l’emblème de la RDC dans l’en-tête de chaque page.

- Parcours guidé en quatre étapes pour composer les onze modèles avec les données d’un dossier agent, d’un service ou de pièces transmises.
- Base agents locale IndexedDB dans la démonstration et dossiers persistants privés dans Django ; création, modification et sélection des dossiers.
- Brouillons documentaires conservant une copie des données et du texte, avec référence et événement dans le circuit de validation.
- Connexion comme point d’entrée à l’ouverture, page de connexion enrichie d’un parcours explicatif et textes agrandis.

- Premier atelier local de sélection et de prévisualisation de documents à partir d’agents fictifs.
- Génération A4 d’une attestation de travail de nuit et d’une notification administrative avec l’emblème fourni et la mention « SPÉCIMEN — NON VALABLE ».
- Téléchargement PDF et tests des routes, des paramètres et des réponses.
- Mention de l’indépendance des projets SIGDA et SSDC dans le README et l’atelier.
- Démonstration statique pour GitHub Pages avec deux dossiers fictifs, deux modèles et quatre spécimens téléchargeables.
- Tableau de bord avec navigation latérale, recherche de dossiers dans la démonstration publique et thèmes clair et sombre.
- Connexion simulée pour la démonstration publique et contrôle des accès par session pour Django.
- Menu rétractable et barres de défilement coordonnées aux deux thèmes, y compris dans l’aperçu.
- Installation de SIGDA en PWA avec page de reprise hors connexion.
- Demandes persistantes dans Django avec soumission, décision par un compte distinct et historique.
- Commande Imprimer dans les deux ateliers, avec mise en page A4 centrée sur le spécimen.
- Pilotage des demandes sur 7, 30 ou 90 jours avec journal, flux, taux d’approbation, médiane et 90ᵉ percentile.
- Navigation par vues distinctes dans Django et sur GitHub Pages. La démonstration simule le traitement des demandes et calcule les indicateurs de l’onglet.
- Ressources de la démonstration versionnées à chaque compilation et HTML revalidé par le service worker.
- Accueil et transitions visuelles modernisés, catalogue par famille et trois nouveaux modèles A4 : attestation de service, convocation administrative et bordereau de transmission.
- Bouton Exit dans le menu et commandes de zoom jusqu’à 200 % pour l’aperçu du spécimen.
- Identité visuelle inspirée de SSDC, police DM Sans hébergée localement et thème clair atténué.
- Assistant documentaire guidé localement et connexion GPT côté serveur configurable par clé API.
- Catalogue étendu à onze modèles et trois styles rédactionnels, soit 66 versions de spécimens A4 pour les deux dossiers fictifs.
- Gabarits d’attestation et de correspondance rapprochés des exemples fournis, bordereau avec tableau des pièces et sources institutionnelles documentées.
- Éditeur du corps du texte dans Django avec variation locale, reformulation GPT optionnelle, contrôle des identités et chiffres, puis application explicite à l’aperçu imprimable.
- Pied de page institutionnel inspiré de l’attestation de service fournie, avec bande tricolore, coordonnées sur deux lignes et QR vectoriel cliquable.
- Fiche publique de lecture du QR avec référence, modèle, date, style et empreinte du texte appliqué, sans prétention d’authentification.
- Accueil enrichi d’accès guidés, repères institutionnels discrets et catalogue latéral sur grand écran pour donner davantage de place à l’aperçu.
- Corps des documents en Times New Roman incorporée dans le PDF, avec composition à 12 points et ajustement A4 si nécessaire.
- Interface en Manrope, textes agrandis, thème Soleil ivoire et sable et barres de défilement coordonnées à leurs surfaces.
- Menus de sélection harmonisés sur les navigateurs compatibles et page hors ligne alignée sur la palette Soleil.

## Circuit nominatif et pilotage DIRCAB — 11 novembre 2026

- Quatre profils distincts OPS, SECAD, AP et DIRCAB, attribution nominative des tâches et échéances facultatives.
- Retours motivés, corrections versionnées, cycles de revalidation et refus final.
- Impression après validation finale uniquement ; archivage du PDF final, SHA-256 et journal des ouvertures côté serveur.
- Activité globale réservée à DIRCAB, séries temporelles, charge et retards par étape, boîte de distribution, médiane/P90, intervalle de Wilson et tableaux de valeurs.
- Quatre comptes de démonstration, circuit et historique conservés localement sur GitHub Pages ; contrôles réels côté Django.

## Cabinet, maintenance et interface scientifique — 11 novembre 2026

- Retrait de première ligne au centre de chaque paragraphe du corps documentaire, en aperçu et à l’impression.
- Police EB Garamond du mode Scientifique d’EduPay, embarquée sous licence OFL ; corps documentaire Times New Roman conservé.
- Affichage/masquage du mot de passe, masquage à la soumission et au changement de visibilité.
- Ajout et correction des agents réservés à la maintenance, imports CSV transactionnels et demandes d’intervention.
- Validité initiale du 1er janvier au 31 décembre 2027, rappel et renouvellement technique journalisé ; archives validées accessibles après échéance.
- Menu mobile latéral accessible, formulaires et dossiers adaptés, tailles tactiles et graphiques mobiles renforcés.
- Identité visuelle PWA SIGDA distincte, icône maskable et Apple ; identifiants stables et consignes par système.

- Micro-interactions, indicateurs pendant les traitements réels et transitions respectant la réduction des animations.
- Fenêtre centrée de confirmation ou d’échec, accessible au clavier, pour les opérations et validations de saisie.

- Emblème de la RDC en filigrane très léger (4,5 %) derrière la zone d’écriture, dans l’aperçu et le PDF ; texte pleinement opaque et en-tête conservé.

## Ergonomie, profils et protections — 12 novembre 2026

- Menu mobile fermé dès le premier affichage, transitions d’ouverture et de fermeture, fermeture par X.
- Icônes œil ouvert/barré pour le mot de passe ; taille de texte adaptée et raccourcis mobiles.
- Indicateur de traitement contextualisé pour la connexion, l’enregistrement et la navigation ; état occupé accessible et réinitialisation au retour de page.
- Services d’affectation contrôlés et tableaux de bord propres aux quatre profils.
- Icônes PWA basées sur l’emblème de la RDC, avec nouvelles URL et identifiant SIGDA conservé.
- Limitation des connexions, en-têtes et sessions renforcés, configuration HTTPS explicite.
- Liseuse grand format du document créé ou enregistré : zoom, largeur, page entière et fermeture au clavier, avec impression toujours soumise au circuit de validation.
- Réduction progressive du menu sur ordinateur, rail d’icônes conservé, apparition séquencée du menu mobile et bouton animé.

- Pied de page commun aux onze modèles : deux lignes de coordonnées, sept icônes et liens sociaux officiels référencés, liens PDF actifs et marge d’impression préservée.
- ADN documentaire versionnée : UUID, révision, SHA-256 du contenu, QR et vérification privée journalisée ; empreinte du PDF final distincte.
- Guide illustré couvrant les cinq espaces et toutes les captures, distribué uniquement sur la connexion de démonstration avec contrôle SHA-256.
- Tableau de bord Maintenance, file centrale des demandes et réponses, détection des mises à jour, filtres et journaux paginés ; simulation locale explicite sur Pages.
- Suppression de la seule confirmation de connexion réussie ; conservation de la journalisation et des autres fenêtres de résultat.
