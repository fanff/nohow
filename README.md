# Outil pour un apprentissage plus rapide

Cet outil est conçu pour accélérer l'apprentissage en utilisant des résumés de livres structurés en chapitres et sous-chapitres. L'utilisateur peut alimenter l'outil avec la structure d'un livre sur n'importe quel sujet. En cliquant sur un chapitre, l'utilisateur peut voir une "génération unique par IA" concernant ce chapitre, dans une conversation avec l'IA. Chaque message se réfère au flux de conversation actuel et donc au chapitre sélectionné. L'utilisateur cherche principalement à comprendre le chapitre et peut poser des questions. L'IA agit comme un assistant d'apprentissage pour expliquer des concepts et répondre aux questions.

## Composants

### Base de données
- Livres -> Arbre de chapitres -> Conversation pour chaque feuille de l'arbre des chapitres

### Frontend
- Écran avec un éditeur de chapitres, structuré comme un arbre avec des nœuds et des branches. Chaque nœud est une chaîne "nom du chapitre" + (descriptions courtes ?). L'utilisateur édite manuellement la structure des chapitres au départ.
- Importation de markdown pour extraire la structure des chapitres.
- Écran avec un fil d'Ariane du chapitre actuel et le titre du chapitre, + conversation.

### Ingénierie des prompts
- Un prompt pour "développer" un sous-chapitre, la première fois que l'utilisateur l'ouvre.
- Un prompt pour discuter généralement avec le chapitre actuel du livre (comme une conversation amorcée avec le contenu + prompt + question de l'utilisateur => réponse).
