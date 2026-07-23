# Jeux de données pour les tests

Fichier de référence pour les tests automatisés (navigateur headless).  
Chaque section contient les paires d'individus attendues et le résultat de relation attendu.

---

## Jeu de données : famille basique

Arbre simple : 3 générations, une branche principale.

```
G1 : Jean DUPONT (1900-1980) ─── Marie MARTIN (1905-1990)
        │
        ├── G2 : Pierre DUPONT (1930-2010) ─── Claire MOREAU (1935-)
        │           │
        │           ├── G3 : Sophie DUPONT (1960-)
        │           │
        │           └── G3 : Marc DUPONT (1965-)
        │
        └── G2 : Louise DUPONT (1932-2020)
                    │
                    └── G3 : Thomas BERTRAND (1962-)
```

### Tests de recherche

| Saisie | Individus attendus |
|--------|-------------------|
| `Jean DUPONT` | Jean DUPONT (1900-1980) |
| `jean dup` | Jean DUPONT |
| `jean` | Jean DUPONT |
| `dupont` | Jean, Pierre, Sophie, Marc DUPONT |
| `Sophie` | Sophie DUPONT (1960-) |
| `soph dup` | Sophie DUPONT |
| `Marie MARTIN` | Marie MARTIN (1905-1990) |
| `marie` | Marie MARTIN |
| `Thomas BERTRAND` | Thomas BERTRAND (1962-) |
| `chl ffer` | ❌ Aucun individu dans cet arbre |

### Tests de relation

| Individu A | Individu B | Relation attendue | Degrés |
|-----------|-----------|-------------------|--------|
| Jean DUPONT | Sophie DUPONT | descendant (3 degrés) |
| Jean DUPONT | Marc DUPONT | descendant (3 degrés) |
| Sophie DUPONT | Marc DUPONT | frère/sœur (2 degrés) |
| Pierre DUPONT | Thomas BERTRAND | oncle → neveu (2 degrés) |
| Louise DUPONT | Sophie DUPONT | tante → nièce (2 degrés) |
| Jean DUPONT | Thomas BERTRAND | descendant (3 degrés) |

**Format attendu pour Sophie ↔ Marc (frères) :**
```
Sophie DUPONT
    père
        Jean DUPONT
    mère
        Marc DUPONT
```

**Format attendu pour Jean ↔ Sophie (aïeul → petite-fille) :**
```
Jean DUPONT
    fils
        Pierre DUPONT
    fille
        Sophie DUPONT
```

**Format attendu pour Jean ↔ Thomas (aïeul → arrière-petit-neveu) :**
```
Jean DUPONT
    fils
        Pierre DUPONT
    fille
        Louise DUPONT
            fils
                Thomas BERTRAND
```

> ⚠️ **Note** : L'algorithme BFS doit trouver le chemin le plus court. Le format d'affichage montre chaque saut sur une ligne avec tabulation, direction ascendante ou descendante.

### Tests d'erreurs

| Cas | Résultat attendu |
|-----|-----------------|
| Même individu (Jean DUPONT ↔ Jean DUPONT) | « Il s'agit de la même personne. » |
| Deux individus de branches disjointes | « Aucun lien de parenté trouvé. » |
| Recherche sans résultat | « Aucun individu ne correspond. » |

---

## Jeu de données : cas edge

### Cas 1 : couple sans enfant

```
G1 : Paul (1950-) ─── Sophie (1952-)    (pas d'enfants)
```

- Recherche `Paul` → trouve Paul
- Recherche `Sophie` → trouve Sophie
- Relation `Paul ↔ Sophie` → « Époux/épouse » (si géré) ou relation directe 1 degré

### Cas 2 : individu sans père ni mère

```
G1 : Orphelin (1980-)
```

- Prévisualisation : père = « inconnu », mère = « inconnue » (ou champ vide)

### Cas 3 : individu sans dates

```
G1 : X (dates inconnues) ─── Y
```

- Prévisualisation : afficher « dates inconnues » au lieu de planter

---

## Jeu de données : accentuation

Tests de recherche sans accent → doit trouver les individus avec accents.

| Saisie | Trouve |
|--------|--------|
| `Chloe Zufferey` | Chloé Zufferey |
| `clemence` | Clémence |
| `noel` | Noël |
| `veronique` | Véronique |
| `lucien beauchene` | Lucien Beauchêne |

---

## Jeu de données : sous-chaînes (substring)

| Saisie | Doit trouver | Pourquoi |
|--------|-------------|----------|
| `chl` | Chloé | « chl » dans « Chloé » |
| `ffer` | Zufferey | « ffer » dans « Zufferey » |
| `chl ffer` | Chloé Zufferey | « chl » AND « ffer » |
| `ém` | Clémence, Clément | « ém » dans « Clémence », « Clément » |
| `ph` | Philippe, Sophie | « ph » dans « Philippe », « Sophie » |
| `x` | Lucien | « x » dans « Lucien » |

---

## Jeu de données : performance

- Fichier GED de test avec **5 000 individus minimum** pour valider :
  - Chargement < 10 secondes
  - Calcul de relation < 2 secondes
