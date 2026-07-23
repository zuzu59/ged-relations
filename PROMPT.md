GED relations 

J'ai un fichier GED d'un arbre généalogique de plusieurs milliers d'individus et je veux afficher, sous forme texte lisible la relation la plus courte entre deux individus via une page web. 

Pour cela je veux serveur en python qui demande via un formulaire js les 2 individus avec une recherche full texte multi string (avec un 'and' entre les strings) dans les champs nom et prénom avec élimination des lettres accentuée avec prévisualisation sur forme liste le résultat à choisir. 
Du style pour Chloé Zufferey, je dois pouvoir la trouver avec
Chloé Zufferey
Chloe Zufferey
chlo zuff
chl ffer
La db, sqlite, doit être chargée avec le fichier GED au moment du démarrage du backend
Le formulaire doit être multi utilisateur, c'est-à-dire que plusieurs personnes puissent faire une recherche de relations en même temps.
Pendant la recherche il faut afficher la date de naissance (et de décès du présent) avec le père et la mère (filiation) afin de pouvoir trouver le bon individu.
Le résultat doit être affiché sous format texte avec tabulation facilement lisible. On doit avoir un bouton exporter en PDF avec une jolie présentation.
Je veux aussi un bouton exporter le résultat sous format GED.
le serveur web doit tourner en 0.0.0.0:8082





.