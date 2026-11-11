# Architecture de SIGDA

SIGDA et SSDC sont des projets indépendants. SIGDA aura ses propres comptes, données, déploiements et procédures d’exploitation.

## Atelier livré

Le serveur Django présente onze modèles et deux agents fictifs. Un compte Django et sa session donnent accès à l’atelier et à ses documents. La sélection transmet les identifiants du catalogue et un style rédactionnel parmi trois variantes préparées. Les PDF sont marqués comme spécimens et leurs réponses interdisent la mise en cache. L’aperçu, l’impression et le téléchargement utilisent le même générateur A4. Les agents et modèles en mémoire sont réservés à cet atelier local.

L’éditeur peut soumettre le corps du texte au serveur pour vérifier les identités et chiffres connus, puis produire un PDF et un aperçu conservés en mémoire dans le navigateur. Le gabarit institutionnel reste composé par le serveur. La rédaction personnalisée n’est pas encore persistée ni liée aux transitions d’une demande. Les demandes et leurs événements sont enregistrés séparément en SQLite avec contrôle d’accès et séparation entre demandeur et valideur.

L’Assistant dispose d’un guidage local par correspondance de termes. Le mode GPT optionnel appelle l’API Responses depuis le serveur avec une clé issue de l’environnement, jamais livrée au navigateur. La reformulation transmet le corps du texte à OpenAI uniquement lorsque l’utilisateur choisit cette action. Les sorties sont proposées à la relecture et ne modifient ni le statut d’une demande ni les gabarits.

La PWA de démonstration publique simule la connexion sur GitHub Pages. Elle publie uniquement des données fictives. Pour la démonstration et l’atelier local, le service worker conserve seulement la page de reprise hors connexion.

## Architecture cible

```mermaid
flowchart LR
    UI[Interface React et PWA] --> API[API Django REST]
    UI --> OIDC[Fournisseur d’identité institutionnel]
    API --> OIDC
    API --> DB[(PostgreSQL)]
    API --> Queue[File de génération]
    Queue --> Worker[Service de génération documentaire]
    Worker --> Store[(Stockage documentaire privé)]
    API --> Store
    Public[Consultation publique par identifiant opaque] --> Verify[API de vérification]
    Verify --> Status[(Statuts publics minimaux)]
```

Le service de vérification expose uniquement le statut, la référence, la date et une catégorie générique. Les dossiers agents, les pièces et les rémunérations restent dans le périmètre privé. Le service worker utilise une liste explicite de ressources statiques. Les parcours protégés exigent une connexion au serveur.

## Modèle de données à implémenter

| Entité | Rôle et contraintes |
| --- | --- |
| Agent | Matricule unique, service et fonction. Affectations et grades historisés. |
| Dossier et pièce | Un dossier par agent. Chaque version de pièce possède sa propre empreinte et un objet privé. |
| Modèle et version | Une catégorie documentaire référence une version de modèle validée et ses champs autorisés. |
| Demande et transition | La demande référence l’agent et la version du modèle. Chaque transition journalise l’auteur, la date et le motif. |
| Document et émission | Le brouillon peut être régénéré. L’émission fige le fichier, sa référence et son empreinte. |
| Séquence de référence | Une séquence par direction et année. Attribution dans la même transaction que l’émission avec contrainte d’unicité. |
| Rémunération | Ressource distincte avec habilitation et journalisation des consultations. |
| Vérification | Identifiant opaque et statut de délivrance ou de révocation. |

## Invariants à vérifier avant une recette institutionnelle

- L’identité institutionnelle et l’habilitation métier sont vérifiées côté serveur à chaque action protégée.
- L’accès à une demande ou à une pièce vérifie la ressource demandée, le périmètre du compte et son rôle.
- L’approbation, la signature, la délivrance et la révocation sont des opérations distinctes. Les circuits soumis à la séparation des fonctions refusent l’auto-approbation.
- L’émission lie la référence à la version exacte du modèle et à l’empreinte du fichier final. Une révocation modifie le statut de vérification et conserve la trace de la décision.
- L’atelier de démonstration et le système institutionnel utilisent des déploiements et des jeux de données séparés.
