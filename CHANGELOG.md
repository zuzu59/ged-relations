# Journal des modifications (Changelog)

Le format de ce journal suit les directives [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/)
et cette application respecte le [Versionnage sémantique](https://semver.org/lang/fr/).

## [0.0.48] — 2026-07-23 à 18h45

### Ajouté
- **Titre cliquable** : Le titre "GED Relations" en haut à gauche est maintenant un lien qui ramène à la racine depuis toutes les pages
- **Page About** : Affichage de la branche git actuelle et lien GitHub correct

### Corrigé
- **Export GED** : Correction du format et des tags obligatoires (GEDC, SOUR, FAMS, FAMC)
- **Export PDF** : Nom de fichier personnalisé avec date/heure
- **Serveur** : Correction erreur NameError sur `current_branch` dans la fonction `index()`
- **Serveur** : Nettoyage des processus Python et caches .pyc avant redémarrage

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
