# Journal des modifications (Changelog)

Le format de ce journal suit les directives [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/)
et cette application respecte le [Versionnage sémantique](https://semver.org/lang/fr/).

## [0.0.37] — 2026-07-23

### Modifié
- Format de la relation : indentation dynamique (monter +1 tab, descendre -1 tab)
- Export PDF : nom de fichier individuel, titre avec accent, date avec heure, version en footer
- Corrections diverses du parser GEDCOM (FAMS/FAMC)

---

## [0.0.36] — 2026-07-23

### Corrigé
- Bouton "Calculer" désactivé : `inputId` non passé à `renderResults` dans `app.js`
- Test data GED : ajout des tags FAMS/FAMC manquants, GEDC/SUBM sous HEAD, SOUR valide
- Parser GEDCOM : deuxième passe pour résoudre les FAMC non résolus

---

## [0.0.35] — 2026-07-23

### Corrigé
- Application complète : backend Flask, parser GEDCOM, BFS, exports PDF/GED
- Menu hamburger avec navigation
- Pages À propos et Aide
- Versionning automatique (version.txt incrémenté au démarrage)
- Rate limiting (10 req/min par IP)
- Données de test dans `test_data.ged`

---

## [0.0.34] — 2026-07-23

### Ajouté
- Format texte des relations : une ligne par saut, tabulations, sans limite de profondeur
- Support des directions multiples (montée/descente dans l'arbre)

---

## [0.0.33] — 2026-07-23

### Ajouté
- Tests headless par version avec Playwright
- Fichier `TESTS-DATA.md` (jeux de données, recherche, relations, edge cases, performance)
- Critère d'acceptation AC13 : tests headless avant chaque version

---

## [0.0.32] — 2026-07-23

### Ajouté
- Menu hamburger avec panneau de navigation
- Page "À propos" (version, date, stack, licence, lien dépôt GitHub)
- Page "Aide" (explications de recherche, exemples, format de résultat, exports)
- Critères d'acceptation AC10–AC12

---

## [0.0.31] — 2026-07-23

### Ajouté
- Système de versionning : pied de page avec version/date
- `CHANGELOG.md` au format Keep a Changelog
- Incrément automatique de la version à chaque démarrage

---

## [0.0.30] — 2026-07-23

### Modifié
- Spécifications refactorisées : structure claire, critères d'acceptation détaillés, cas limites
- Recherche par sous-chaîne (LIKE '%mot%') au lieu de prefix
- Anti-accentuation (Chloé ≡ Chloe)

---

## [0.0.1] — 2025-07-15

### Ajouté
- Premiers commits du projet
- Structure initiale du dépôt
