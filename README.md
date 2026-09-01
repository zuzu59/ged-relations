# GED Relations

Application web permettant de calculer et afficher la relation la plus courte entre deux individus au sein d'un arbre généalogique stocké dans un fichier GED (GEDCOM).

![Version](https://img.shields.io/badge/version-0.0.49-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)

## 🌟 Fonctionnalités

- **Recherche full-text** : Recherche d'individus par nom (sous-chaîne, anti-accentuation)
- **Calcul de relation** : Algorithme BFS pour trouver le lien de parenté le plus court
- **Affichage arborescent** : Visualisation des relations avec indentation dynamique
- **Exports** :
  - PDF avec titre et date d'export
  - GEDCOM 5.5.1 avec tags FAMS/FAMC
- **Interface responsive** : Menu hamburger, pages À propos et Aide
- **Multi-utilisateur** : Support de plusieurs recherches simultanées
- **Rate limiting** : 10 requêtes/min par IP

## 🚀 Installation

### Prérequis

- Python 3.11 ou supérieur
- pip ou uv

### Installation

```bash
# Cloner le dépôt
git clone https://github.com/zuzu59/ged-relations.git
cd ged-relations

# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
# ou avec uv
uv pip install -r requirements.txt
```

## 📖 Utilisation

### Lancer l'application

```bash
Le plus simple :

# utiliser ce script pour la prod (port 8082)
./start-prod.sh

# utiliser ce script pour la dev (port 8092)
./start-dev.sh

Ou alors :

# Avec un fichier GED spécifique et un port
python app.py chemin/vers/fichier.ged --port 8082

# Avec le fichier de test par défaut en dev
python app.py test_data.ged --port 8092

# Sans argument (utilise test_data.ged si présent)
python app.py --port 8082
```

L'application démarre sur : **http://0.0.0.0:8082** en prod et **http://0.0.0.0:8092** en dev.

### Interface web

1. **Rechercher** : Saisir un nom dans les champs de recherche (ex: "Jean", "Dupont")
2. **Sélectionner** : Cliquer sur un individu dans les résultats
3. **Calculer** : Cliquer sur "Calculer" pour trouver la relation
4. **Exporter** : Télécharger le résultat en PDF ou GED

### Exemples de recherche

- Recherche par prénom : `Jean`
- Recherche par nom : `DUPONT`
- Recherche avec accents : `Chloé` (trouve aussi `Chloe`)
- Recherche partielle : `ph` (trouve `Sophie`)

## 📁 Structure du projet

```
ged-relations/
├── app.py                 # Application Flask principale
├── gedcom_parser.py       # Parser GEDCOM 5.5.1 / 7.0
├── graph.py               # Algorithme BFS pour relations
├── pdf_export.py          # Export PDF
├── ged_export.py          # Export GEDCOM
├── version.py             # Gestion de version
├── requirements.txt       # Dépendances Python
├── test_data.ged          # Jeu de données de test
├── CHANGELOG.md           # Historique des versions
├── TESTS-DATA.md          # Jeux de données de test
├── templates/
│   ├── base.html          # Template de base
│   ├── index.html         # Page principale
│   ├── about.html         # Page À propos
│   └── help.html          # Page Aide
├── static/
│   ├── style.css          # Styles CSS
│   └── app.js             # JavaScript frontend
└── screencopy/            # Captures d'écran
```

## 🛠️ Technologies

- **Backend** : Python 3.11, Flask, SQLite
- **Frontend** : HTML5, CSS3, JavaScript vanilla
- **Exports** : fpdf2 (PDF), GEDCOM 5.5.1
- **Tests** : Playwright (headless browser)
- **Développement** : uv (gestionnaire de paquets)

## 📝 Format des relations

Les relations s'affichent avec une indentation dynamique :
- **Monter** (ancêtres) : +1 tab
- **Descendre** (descendants) : -1 tab
- **Exemple** :
  ```
  Jean DUPONT
      Pierre DUPONT
          Sophie DUPONT
  ```

## 🔍 Recherche

- **Sous-chaîne** : `LIKE '%mot%'` (pas de prefix matching)
- **Multi-mots** : AND entre mots (ex: `Jean DUPONT`)
- **Anti-accentuation** : `Chloé` ≡ `Chloe`

## 📄 Exports

### PDF
- **Nom** : `individu1_individu2-yyymmdd.hhmm.pdf`
- **Titre** : "GED Relations - Rapport de parenté"
- **Date** : Avec heure et minutes

### GEDCOM
- **Format** : GEDCOM 5.5.1
- **Tags** : GEDC, SOUR, FAMS, FAMC
- **Nom** : `individu1_individu2-yyymmdd.hhmm.ged`

## 🧪 Tests

```bash
# Tests headless avec Playwright
python -m pytest tests/ -v
```

Voir `TESTS-DATA.md` pour les jeux de données.

## 📚 Documentation

- [PROMPT2.md](PROMPT2.md) : Spécifications fonctionnelles
- [CHANGELOG.md](CHANGELOG.md) : Historique des versions
- [TESTS-DATA.md](TESTS-DATA.md) : Jeux de données de test

## 🤝 Contribution

Les contributions sont les bienvenues !

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amazing`)
3. Committer (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing`)
5. Ouvrir une Pull Request

## 📄 License

MIT License - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👤 Auteur

**Christian Zufferey**
- GitHub: [@zuzu59](https://github.com/zuzu59)
- Email: christian@zufferey.com

## 🙏 Remerciements

- [GEDCOM](https://wiki.gedcom.org/) pour le standard de fichiers généalogiques
- [Flask](https://flask.palletsprojects.com/) pour le framework web
- [fpdf2](https://py-pdf.github.io/fpdf2/) pour la génération PDF
- [Playwright](https://playwright.dev/) pour les tests headless

---

**Développé avec ❤️ par Christian Zufferey**
