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
- Afficher le résultat sous forme **textuelle avec tabulations**, facilement lisible.
- Exemple de format :
  ```
  Lien de parenté le plus court : 3 degré(s)
  
  [Individu A] → père → [Intermédiaire 1] → mère → [Intermédiaire 2] → fils → [Individu B]
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
│  GED Relations                              │
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
│  Lien de parenté le plus court : 3 degré(s) │
│                                             │
│  [Individu A] → père → ... → [Individu B]  │
│                                             │
│  [Exporter en PDF]  [Exporter en GED]      │
│                                             │
└─────────────────────────────────────────────┘
```

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
- [ ] **AC05** — Le résultat est affiché en texte tabulé, lisible.
- [ ] **AC06** — Deux requêtes simultanées ne se perturbent pas mutuellement.
- [ ] **AC07** — L'export PDF produit un document présentable avec les informations de relation.
- [ ] **AC08** — L'export GED génère un fichier GED valide contenant uniquement le sous-chemin de relation.
- [ ] **AC09** — Un arbre de plusieurs milliers d'individus est traité en moins de 10s au démarrage et < 2s par calcul.

---

## Évolutions futures

- [ ] Authentification des utilisateurs
- [ ] Sauvegarde d'historique des recherches
- [ ] Carte visuelle de la relation (graphique)
- [ ] Support de plusieurs fichiers GED
- [ ] Filtrage avancé (par date, lieu, etc.)
