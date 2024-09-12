# argentiere-tracking
Ce repo git s'appuie sur la bibliothèque PyTrx, qu'il est nécessaire d'installer et de placer dans le même dossier pour pouvoir utiliser les scripts de tracking. (cf. le gitignore)

Notre démarche a été d'essayer d'exploiter les codes écrits par Penelope How et son équipe, qui se sont révélés obsolètes et qui n'ont pas fonctionné en l'absence d'images de calibration de notre caméra.
Nous avons donc réutilisé les briques de base disponibles dans PyTrx, et non les boites noires "all-inclusive" de Pytrx, qui utilisent une approche convolutée. Le script que nous avons donc utilisé est argentiere.py, avec l'environnement disponible sur notre repo (l'environnement proposé sur le repo PyTrx ne permet pas de faire tourner PyTrx).
