# GED Relations — Application de Recherche de Relations Généalogiques

## Vue d'ensemble

Application web permettant de calculer et afficher **la relation la plus courte** entre deux individus au sein d'un arbre généalogique stocké dans un fichier GED (GEDCOM).

**Stack technique :**
- **Backend :** Python
- **Base de données :** SQLite (chargée depuis le fichier GED au démarrage)
- **Frontend :** HTML / CSS / JavaScript
- **Serveur :** `0.0.0.0:8082`

**Objectif :** Deux utilisateurs peuvent effectuer simultanément des recherches de relations via une interface web avec autocomplétion, prévisualisation des individus, et export des résultats.

---

## Spécifications fonctionnelles

### Recherche d'individus (Must)

- Formulaire de saisie double (2 individus) avec recherche full-text multi-mots.
- Les mots de recherche sont combinés avec un opérateur `AND`.
- Recherche dans les champs **nom** et **prénom**.
- **Élimination des caractères accentués** lors de la comparaison (ex: `Chloé` ≡ `Chloe`).
- **Prévisualisation** des résultats sous forme de liste sélectionnable.
- **Stratégie de recherche** : chaque mot fait un `LIKE '%mot%'` (sous-chaîne) sur nom et prénom, combinés par `AND`. Chaque mot de la saisie doit apparaître **n'importe où** dans le nom ou le prénom.

**Exemples de recherches valides pour "Chloé Zufferey" :**
| Saisie | Résultat |
|--------|----------|
| `Chloé Zufferey` | ✅ Trouvé |
| `Chloe Zufferey` | ✅ Trouvé (sans accent) |
| `chlo zuff` | ✅ Trouvé (mots partiels) |
| `chl ffer` | ✅ Trouvé (sous-chaînes de `Chloé Zufferey`) |
| `xyz` | ❌ Aucun résultat |

### Informations de prévisualisation (Must)

Pour chaque individu dans la liste de résultats, afficher :
- **Nom complet** (prénom + nom)
- **Date de naissance**
- **Date de décès** (si l'individu est décédé)
- **Filiation** : nom du père et de la mère
- **Identifiant unique** GED (ex: `@I1@`) pour référence interne

Ces informations permettent à l'utilisateur d'identifier le bon individu parmi les résultats.

### Calcul de relation (Must)

- Calculer **la relation la plus courte** (graphe non orienté, BFS) entre les deux individus sélectionnés.
- Afficher le résultat sous forme **textuelle avec indentation (tabulations)**, une relation par ligne, sans limite de profondeur.
- **Chaque ligne** représente un saut de relation (père, mère, fils, fille, époux, etc.).
- **L'indentation** montre la profondeur par rapport à l'individu 1 : 0 tab = individu 1, 1 tab = son parent, 2 tabs = son grand-parent, etc.
- La relation peut aller **vers le haut** (aïeux), **vers le bas** (descendants), ou **les deux** (ex: monter vers un ancêtre commun puis redescendre).
- Exemple de format :
  ```
  Lien de parenté le plus court : 3 degré(s)

  Individu 1
      père
          grand-père paternel
      mère
          individu 2
  ```
- Autre exemple (relation descendante uniquement) :
  ```
  Individu 1
      fils
          petit-fils
      fille
          individu 2
  ```
- Autre exemple (relation montante puis descendante) :
  ```
  Individu 1
      père
          grand-père
      mère
          tante
              individu 2
  ```

### Multi-utilisateur (Must)

- Le serveur doit supporter **plusieurs requêtes simultanées** (recherches de relations en parallèle).
- Aucune interfereance entre les sessions de différents utilisateurs.
- **Rate limiting** : 10 requêtes de recherche par minute par IP pour prévenir les abus.

### Exports (Should)

#### Export PDF (Should)
- Bouton d'export du résultat de relation en **format PDF**.
- Présentation soignée et lisible (en-tête avec les noms des deux individus, tableau des liens, date d'export).

#### Export GED (Should)
- Bouton d'export du résultat de relation en **format GED**.
- Le fichier GED généré doit contenir uniquement les individus et liens composant le chemin de relation.

---

## Spécifications techniques

### Chargement du fichier GED

- Le fichier GED est chargé **au démarrage du serveur** (une seule fois).
- Support **GEDCOM 5.5.1 et 7.0** (extensions `.ged`, `.gedcom`).
- Parsing du format GEDCOM pour extraire :
  - Les individus (`@...@ INDI`) : nom, prénom, dates de naissance/mort
  - Les couples (`HUSB`, `WIFE`)
  - Les enfants (`CHIL`)
- Construction d'un **graphe de parenté** en mémoire (SQLite ou structure équivalente).

### API / Interface

- **Page web unique** avec formulaire de recherche intégré.
- Recherche full-text côté serveur ou côté client (au choix, performance primordiale).
- Les recherches sont **indépendantes** entre utilisateurs (pas de verrouillage).

### Performance

- Le temps de calcul de la relation la plus courte doit rester **raisonnable** (< 2 secondes) pour un arbre de plusieurs milliers d'individus.
- Le chargement initial du GED doit être **rapide** (< 10 secondes).
- Interface **responsive** : utilisable sur desktop et mobile.

### Cas particuliers

- **Individus disjoints** (arbres séparés) : « Aucun lien de parenté trouvé entre ces deux individus. »
- **Individu non trouvé** : « Aucun individu ne correspond à votre recherche. »
- **Même individu** : « Il s'agit de la même personne. »

---

## Interface utilisateur

### Page principale

```
┌─────────────────────────────────────────────┐
│  GED Relations                          [☰] │
├─────────────────────────────────────────────┤
│                                             │
│  Individu 1 : [________________]  [✓]      │
│  (liste de prévisualisation ci-dessous)     │
│                                             │
│  Individu 2 : [________________]  [✓]      │
│  (liste de prévisualisation ci-dessous)     │
│                                             │
│  [Calculer la relation]                     │
│                                             │
├─────────────────────────────────────────────┤
│  Résultat :                                 │
│                                             │
│  Lien de parenté : 3 degré(s)               │
│                                             │
│  Individu A                                │
│      père                                  │
│          individu intermédiaire            │
│      mère                                  │
│          Individu B                        │
│                                             │
│  [Exporter en PDF]  [Exporter en GED]      │
│                                             │
│  v0.0.1 — 15 juil. 2025                     │
└─────────────────────────────────────────────┘
```

**Menu hamburger ouvert :**
```
┌──────────────────────────────────────┐
│  GED Relations              [✕]      │
├──────────────────────────────────────┤
│                                      │
│  ───────────────────────────         │
│                                      │
│  [ℹ]  À propos                       │
│  [?]  Aide                           │
│                                      │
│  ───────────────────────────         │
│                                      │
│  v0.0.1 — 15 juil. 2025             │
│                                      │
└──────────────────────────────────────┘
```

### Menu hamburger (Must)

- Icône hamburger (☰) en haut à droite de la page.
- Ouvrant un panneau latéral ou une overlay avec les liens :
  - **À propos** — page "About"
  - **Aide** — page "Help"
- Fermeture du menu par clic sur le fond, le bouton ✕, ou la touche `Échap`.
- Accessible clavier : `Tab` pour naviguer, `Entrée` pour activer, `Échap` pour fermer.
- Accessibilité : `aria-label="Menu"`, `aria-expanded`, `role="button"`.

### Page "À propos" (Must)

- Accessible via le menu hamburger.
- Contient :
  - **Nom de l'application** : GED Relations
  - **Version** : `v0.0.x` (dynamique, identique au pied de page)
  - **Date de compilation** : `dd mmm yyyy`
  - **Description** : courte (1-2 phrases)
  - **Stack technique** : Python, SQLite, HTML/CSS/JS
  - **Licence** : mention de la licence du projet (`LICENSE`)
  - **Lien vers le dépôt** : lien cliquable pointant vers **la branche actuelle** du dépôt GitHub
    - Exemple de texte: `Dépôt GitHub — branche master`
    - URL dynamique selon la branche courante (ex: `https://github.com/zuzu59/ged-relations/tree/master`)
  - **Auteur** : mention si applicable

### Page "Aide" (Must)

- Accessible via le menu hamburger.
- Contient :
  - **Comment rechercher un individu** : explication de la recherche multi-mots avec sous-chaînes
  - **Exemples de recherche** :
    - `Chloé Zufferey` → recherche exacte
    - `Chloe Zufferey` → sans accent
    - `chlo zuff` → mots partiels
    - `chl ffer` → sous-chaînes internes
  - **Comment lire le résultat** :
    - Une ligne par saut de relation
    - Tabulations pour l'indentation (profondeur)
    - Directions possibles : père/mère (vers le haut), fils/fille (vers le bas), époux/épouse
    - Pas de limite de profondeur
    - Exemple :
      ```
      Individu 1
          père
              grand-père
          mère
              individu 2
      ```
  - **Exports** : description des boutons PDF et GED
  - **Limites connues** : cas où aucune relation n'est trouvée (arbres disjoints)

### Comportements

- **Saisie → autocomplétion** : la liste de prévisualisation se met à jour à chaque frappe.
- **Sélection** : cliquer sur un individu de la liste le fixe dans le champ correspondant.
- **Calcul** : affichage du résultat avec les boutons d'export.
- **Recherche à nouveau** : possibilité de changer les individus et recalculer.

---

## Critères d'acceptation

- [ ] **AC01** — Le serveur démarre sur `0.0.0.0:8082` et charge un fichier GED sans erreur.
- [ ] **AC02** — La recherche full-text trouve un individu avec une saisie sans accent, avec des mots partiels (sous-chaîne), ou une combinaison de ceux-ci.
- [ ] **AC03** — La prévisualisation affiche nom, dates de naissance/mort, et filiation (père + mère).
- [ ] **AC04** — Le calcul de la relation la plus courte retourne le chemin minimal correct (vérifié par BFS).
- [ ] **AC05** — Le résultat est affiché avec un saut de ligne par relation, tabulations pour l'indentation, direction ascendante/descendante, sans limite de profondeur.
- [ ] **AC06** — Deux requêtes simultanées ne se perturbent pas mutuellement.
- [ ] **AC07** — L'export PDF produit un document présentable avec les informations de relation.
- [ ] **AC08** — L'export GED génère un fichier GED valide contenant uniquement le sous-chemin de relation.
- [ ] **AC09** — Un arbre de plusieurs milliers d'individus est traité en moins de 10s au démarrage et < 2s par calcul.
- [ ] **AC10** — Le menu hamburger ouvre/ferme correctement et est accessible au clavier.
- [ ] **AC11** — La page "À propos" affiche version, date, stack, licence et lien vers la branche GitHub courante.
- [ ] **AC12** — La page "Aide" contient des explications claires avec exemples de recherche.
- [ ] **AC13** — Chaque version est validée par des tests headless (navigateur) utilisant le jeu de données `TESTS-DATA.md` avant incrémentation.

---

## Tests

### Tests de validation par version (Must)

- **À chaque nouvelle version** (`0.0.x`), exécuter un **jeu de tests réel** avec un **navigateur headless** (ex: Playwright, Puppeteer, ou Selenium) pour vérifier que toutes les fonctionnalités marchent comme demandé.
- Les tests doivent interagir avec l'application comme un **vrai utilisateur** :
  - Remplir les champs de recherche
  - Cliquer dans les listes de prévisualisation
  - Cliquer sur "Calculer la relation"
  - Vérifier le résultat affiché
  - Tester les exports PDF et GED
  - Tester le menu hamburger, les pages À propos et Aide
- Le jeu de données de test est défini dans le fichier **`TESTS-DATA.md`**.
- Les tests sont **automatisés** et doivent passer avant chaque incrémentation de version.
- En cas d'échec, **la version n'est pas incrémentée** — corriger d'abord.

### Outils de test (Should)

- **Playwright** (recommandé) ou Puppeteer pour l'automatisation navigateur headless.
- Tests écrits en **TypeScript** ou **JavaScript**.
- Commande unique pour lancer tous les tests : `npm test` ou `npx playwright test`.

---

## Versionning

### Affichage (Must)

- **Pied de page de chaque page** : afficher la version `0.0.x` et la date de compilation au format `dd mmm yyyy`.
- Exemple : `v0.0.3 — 15 juil. 2025`
- La version est incrémentée automatiquement à chaque compilation (patch : `x + 1`).
- Le backend doit servir la version et la date via un endpoint ou les inclure dans les pages HTML servies.

### Changelog (Must)

- Fichier **`CHANGELOG.md`** au format [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).
- Mis à jour à **chaque changement de version** avec la date, le numéro de version, et la liste des modifications.
- Sections obligatoires: `## [version] - yyyy-mm-dd`, avec sous-sections `Ajouté`, `Modifié`, `Corrigé`, `Supprimé` si pertinent.

---

## Évolutions futures

- [ ] Authentification des utilisateurs
- [ ] Sauvegarde d'historique des recherches
- [ ] Carte visuelle de la relation (graphique)
- [ ] Support de plusieurs fichiers GED
- [ ] Filtrage avancé (par date, lieu, etc.)
