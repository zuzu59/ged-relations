# Journal des modifications (Changelog)

Le format de ce journal suit les directives [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/)
et cette application respecte le [Versionnage sémantique](https://semver.org/lang/fr/).

## [0.0.74] — 2026-09-01 à 10h15

### Changé
- **Démarrage serveur** : `app.py` accepte maintenant le port en argument (`--port`)
- **Scripts** : `start-prod.sh` utilise le port 8082 et `start-dev.sh` utilise le port 8092
- **README** : La documentation de démarrage a été mise à jour pour refléter les nouveaux ports

---

## [0.0.73] — 2026-07-26 à 17h35

### Ajouté
- **Recherche enrichie** : La recherche d'individus fonctionne maintenant sur le nom, le prénom, la date de naissance, la date de décès ET l'ID
- **Affichage de l'ID** : Les résultats de recherche affichent maintenant l'ID de l'individu à côté du nom (ex: `Nom Prénom (I1190314)`) pour faciliter la vérification
- **Styles CSS** : Nouvelle classe `.search-result-item__id` pour le style de l'ID dans les résultats

---

## [0.0.72] — 2026-07-26 à 17h30

## [0.0.71] — 2026-07-26 à 17h25

## [0.0.70] — 2026-07-26 à 17h15

## [0.0.69] — 2026-07-25 à 14h35

## [0.0.68] — 2026-07-25 à 14h30

## [0.0.67] — 2026-07-25 à 01h15

### Corrigé
- **Export GED** : Chaque individu a maintenant un FAMC — expansion automatique des parents pour connecter l'arbre "montant" dans le viewer
- **Export GED** : Plus de familles orphelines ni de familles dupliquées
- **Export GED** : Les époux hors-chemin qui sont parents d'un membre du chemin sont maintenant inclus (ex: I24 mère de I25)

---

## [0.0.66] — 2026-07-25 à 01h00

### Corrigé
- **Export GED** : Suppression des familles en double (F0001/F0002 vs F0006/F0007)
- **Export GED** : Création des familles en une seule passe (parents + enfants ensemble)

---

## [0.0.65] — 2026-07-24 à 19h55

### Corrigé
- **Import GED** : Correction du double encodage UTF-8 (MyHeritage) — les accents (é, è, ê, ë, à, ç, etc.) sont maintenant correctement importés

---

## [0.0.64] — 2026-07-24 à 19h48

### Corrigé
- **Export GED** : Suppression des individus hors chemin (ancêtres superflus, spouses non connecteurs)
- **Export GED** : Ajout des parents connecteurs (relient 2+ personnes du chemin) pour garder la structure familiale
- **Export GED** : Families correctement créées avec un seul parent quand l'autre est hors chemin

---

## [0.0.63] — 2026-07-24 à 17h15

### Changé
- **Import/Export GED** : Migration vers python-gedcom (plus robuste, support UTF-8 natif, GED valide)
- Suppression de ged4py

---

## [0.0.62] — 2026-07-24 à 16h45

### Corrigé
- **Export GED** : Structure correcte (HEAD avec SUBM/FORM, IDs entre @, format noms GEDCOM)

---

## [0.0.61] — 2026-07-24 à 16h35

### Amélioré
- **Affichage web** : Police Helvetica (au lieu de Courier)
- **Affichage web** : Pas de tabulations, juste des espaces pour mobile
- **Outils** : Script `restart.sh` pour redémarrage propre du serveur

---

## [0.0.60] — 2026-07-24 à 16h25

### Amélioré
- **Format relation** : Suppression de 'épouse:' dans l'affichage
- **Export PDF** : Format landscape (paysage) pour plus de place

---

## [0.0.59] — 2026-07-24 à 16h15

### Amélioré
- **Export PDF** : Police Helvetica (plus élégante que Courier)

---

## [0.0.58] — 2026-07-24 à 16h15

### Corrigé
- **Export PDF** : Support du tiret cadratin `—` et autres caractères spéciaux

---

## [0.0.57] — 2026-07-24 à 16h05

### Ajouté
- **Encodage** : Correction du double encodage UTF-8 dans les fichiers GEDCOM
- **Dates** : Format changé en dd/mm/yyyy (4 chiffres pour l'année)
- **Époux(se)** : L'homme est toujours affiché en premier, suivi de la femme
- **Dates des conjoints** : Affichées à côté du nom de l'époux(se)

---

## [0.0.56] — 2026-07-24 à 10h35

### Corrigé
- **Dates** : Format changé en dd/mm/yy
- **Parents** : Affichés uniquement pour les personnes intermédiaires (pas pour les extrémités)

---

## [0.0.55] — 2026-07-24 à 10h30

### Ajouté
- **Dates** : Affichage des dates de naissance et décès pour chaque individu
- **Parents** : Affichage des deux parents sur la même ligne (père en premier)
- **Formattage** : Amélioration de la lisibilité des résultats

---

## [0.0.54] — 2026-07-24 à 10h25

### Corrigé
- **Rate limiting** : Remis à 200 req/min (protection + usage familial)

---

## [0.0.53] — 2026-07-24 à 10h15

### Corrigé
- **Rate limiting** : Désactivé par défaut pour usage familial
- **Multi-utilisateur** : Plus de blocage lors de calculs simultanés

---

## [0.0.52] — 2026-07-23 à 19h45

### Corrigé
- **Relations familiales** : Résolution correcte des père/mère via FAMC
- **Format IDs** : Normalisation des IDs (sans @) dans toute l'application
- **Graphes** : 465 relations calculées avec succès

---

## [0.0.51] — 2026-07-23 à 19h30

### Ajouté
- **Migration ged4py** : Utilisation de la bibliothèque ged4py pour le parsing GEDCOM avec fallback sur un parser simple
- **Support encodages** : Gestion du BOM UTF-8, des fichiers Windows-1252, et des encodages problématiques
- **Support MyHeritage** : Parsing réussi des fichiers exportés par MyHeritage Family Tree Builder

### Modifié
- **Parser GEDCOM** : Architecture hybride (ged4py + fallback simple) pour une meilleure compatibilité

---

## [0.0.50] — 2026-07-23 à 19h20

### Ajouté
- **README.md** : Documentation complète du projet (installation, utilisation, structure, technologies)

---

## [0.0.49] — 2026-07-23 à 19h10

---

## [0.0.48] — 2026-07-23 à 18h45

---

## [0.0.40] — 2026-07-23 à 18h17

### Ajouté
- **Page À propos** :
  - Affichage de la branche git actuelle
  - Lien GitHub vers la branche courante

---

## [0.0.39] — 2026-07-23 à 17h25

### Corrigé
- **Export GED** :
  - Correction du nom de fichier : `individu1_individu2-yyymmdd.hhmm.ged`
  - Utilisation du Content-Disposition de la réponse serveur

---

## [0.0.38] — 2026-07-23 à 17h42

### Corrigé
- **Export GED** :
  - Ajout de `GEDC 5.5.1` et `SOUR GED Relations` sous HEAD
  - Ajout des tags `FAMS` et `FAMC` dans tous les individus
  - Reconstruction des familles (couples + parent-enfant)

---

## [0.0.37] — 2026-07-23 à 16h40

### Ajouté
- **Format de la relation** : indentation dynamique
  - Monter (père/mère) = +1 tab
  - Descendre (fils/fille) = -1 tab
  - Offset automatique
- **Export PDF** :
  - Nom de fichier : `individu1_individu2-yyymmdd.hhmm.pdf`
  - Titre : "GED Relations - Rapport de parenté"
  - Date d'export avec heure et minutes
  - Footer avec version et date de build
- **Parser GEDCOM** :
  - Deuxième passe pour résoudre les FAMC
  - Correction des familles

---

## [0.0.36] — 2026-07-23 à 16h20

### Corrigé
- **Bouton "Calculer" désactivé** : 
  - Problème : `inputId` non passé à `renderResults` dans `app.js`
  - Conséquence : impossible de sélectionner un individu, le bouton restait disabled
  - Solution : passage de `inputId` comme paramètre dans toute la chaîne `initSearch → doSearch → renderResults`
- **Test data GED (`test_data.ged`)** :
  - Ajout des tags `FAMS` manquants dans tous les individus mariés
  - Ajout des tags `FAMC` manquants dans tous les enfants
  - Ajout de `GEDC 5.5.1` et `SUBM @SUBM@` sous HEAD
  - Correction du tag `SOUR` (valide GEDCOM)
- **Parser GEDCOM** :
  - Deuxième passe après le premier chargement pour résoudre les FAMC
  - Association père/mère via les familles quand FAMC est présent

---

## [0.0.35] — 2026-07-23 à 15h53

### Ajouté
- **Application complète** (backend + frontend) :
  - Backend Flask sur `0.0.0.0:8082`
  - Parser GEDCOM 5.5.1 et 7.0 → SQLite
  - Algorithme BFS pour la relation la plus courte
  - Frontend HTML/CSS/JS responsive
- **API REST** :
  - `GET /api/search?q=...` : recherche full-text avec sous-chaînes
  - `POST /api/relation` : calcul de relation entre deux individus
  - `POST /api/export/pdf` : export PDF
  - `POST /api/export/ged` : export GED
- **Menu hamburger** :
  - Panneau de navigation accessible (clavier + souris)
  - Fermeture par Escape ou clic sur overlay
- **Pages** :
  - Page principale avec recherche et affichage des résultats
  - Page "À propos" (version, date, stack, licence, lien GitHub)
  - Page "Aide" (explications, exemples, format de résultat)
- **Versionning automatique** :
  - `version.txt` incrémenté à chaque démarrage
  - Affichage en footer : `v0.0.x — dd mmm yyyy`
- **Rate limiting** : 10 requêtes/min par IP
- **Données de test** : `test_data.ged` avec 18 individus et 8 familles

---

## [0.0.34] — 2026-07-23 à 15h23

### Ajouté
- **Format texte des relations** :
  - Une ligne par saut de relation
  - Tabulations pour l'indentation (profondeur)
  - Support des directions multiples (montée/descente)
  - Pas de limite de profondeur
- **Exemple** :
  ```
  Jean DUPONT
      Pierre DUPONT
          Sophie DUPONT
  ```

---

## [0.0.33] — 2026-07-23 à 15h19

### Ajouté
- **Tests headless avec Playwright** :
  - Validation automatique de l'interface web
  - Tests de navigation, recherche, calcul de relation
  - Tests d'exports PDF/GED
- **Fichier `TESTS-DATA.md`** :
  - Jeux de données de test
  - Cas de recherche (sous-chaînes, accents)
  - Cas de relations (frères, oncle/neveu, disjoints)
  - Cas limites (même personne, personnes disjointes)
- **Critère d'acceptation AC13** :
  - Tests headless obligatoires avant chaque version
  - Validation de tous les critères AC01-AC12

---

## [0.0.32] — 2026-07-23 à 15h19

### Ajouté
- **Menu hamburger** :
  - Bouton menu accessible (aria-expanded)
  - Panneau de navigation latéral
  - Support clavier (Tab, Escape)
- **Page "À propos"** :
  - Version de l'application
  - Date de build
  - Stack technique (Flask, SQLite, fpdf2, Playwright)
  - Licence MIT
  - Lien vers le dépôt GitHub (branche ver1)
- **Page "Aide"** :
  - Exemples de recherche
  - Explication du format de résultat
  - Instructions d'export
  - Limites de l'application
- **Critères d'acceptation AC10-AC12** :
  - AC10 : Menu hamburger fonctionnel
  - AC11 : Page À propos informative
  - AC12 : Page Aide complète

---

## [0.0.31] — 2026-07-23 à 15h19

### Ajouté
- **Système de versionning** :
  - Fichier `version.txt` (format `0.0.x`)
  - Incrément automatique à chaque démarrage de l'application
  - Affichage en footer de chaque page
- **CHANGELOG.md** :
  - Format Keep a Changelog
  - Historique des versions avec catégories (Ajouté, Modifié, Corrigé, Supprimé)
- **Critère d'acceptation AC09** :
  - La version est affichée sur toutes les pages
  - La version s'incrémente à chaque lancement

---

## [0.0.30] — 2026-07-23 à 15h19

### Modifié
- **Spécifications refactorisées** (`PROMPT2.md`) :
  - Structure claire : Vue d'ensemble, Spécifications fonctionnelles, Spécifications techniques
  - Interface utilisateur détaillée avec mockups
  - Critères d'acceptation complets (AC01-AC09)
  - Section "Évolutions futures"
- **Recherche** :
  - Passage du prefix matching à la sous-chaîne (LIKE '%mot%')
  - Support de plusieurs mots (AND entre mots)
  - Anti-accentuation (Chloé ≡ Chloe)
- **Cas limites documentés** :
  - Recherche vide
  - Aucune result
  - Même individu
  - Individus disjoints
  - Performances (10k+ individus)

---

## [0.0.1] — 2026-07-23 à 15h26

### Ajouté
- **Premiers commits du projet** :
  - Initialisation du dépôt GitHub
  - Structure de base du projet
  - Documentation initiale (PROMPT.md)
