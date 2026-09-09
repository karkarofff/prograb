<p align="center">
  <img src="prograb_logo.png" width="140" alt="Logo ProGrab">
</p>

<h1 align="center">ProGrab</h1>

<p align="center">
  Un téléchargeur de vidéos propre et moderne pour Windows — colle un lien, choisis la qualité, terminé.
</p>

<p align="center">
  🇬🇧 <a href="README.md">English version</a>
</p>

---

## C'est quoi ?

ProGrab est une interface minimaliste autour de l'excellent [yt-dlp](https://github.com/yt-dlp/yt-dlp) : colle l'URL d'une vidéo, vois la miniature/le titre/la durée, choisis une qualité, et regarde le bouton de téléchargement se transformer lui-même en barre de progression.

<img width="741" height="660" alt="prograb" src="https://github.com/user-attachments/assets/b87c40ca-f397-4ebe-bcc4-964f40f5eacd" />


## Fonctionnalités

- 🎯 **Flux simple** — coller, analyser, télécharger. Le gros bouton devient la barre de progression (pourcentage, taille, vitesse, temps restant), un clic en plein téléchargement annule, et il passe au vert quand c'est fini.
- 🎞 **Des vrais MP4** — les vidéos sont forcées en H.264 + AAC dès que disponible : les fichiers se lisent partout (vieilles télés comprises), pas seulement dans VLC.
- 🎵 **Mode MP3** — extraction audio seule, convertie en MP3.
- - 📝 **Mode Transcript** — récupère les sous-titres de la vidéo (manuels en priorité, auto-générés sinon) et les convertit en fichier .txt propre : sans timestamps, sans lignes répétées, juste du texte lisible. Parfait pour donner une vidéo à une IA ou survoler une conférence.
- 🔁 **Auto-entretenu** — au premier lancement, ProGrab récupère ses outils (yt-dlp, ffmpeg, deno) dans son dossier de données, puis **yt-dlp se met à jour tout seul en silence à chaque démarrage**. Quand les sites changent, l'app se répare seule. ProGrab prévient aussi quand une nouvelle version de lui-même est disponible.
- 🌑 **Interface sombre moderne** — CustomTkinter, coins arrondis partout, zéro fouillis.
- La qualité choisie est mémorisée comme réglage par défaut entre les sessions.

## Installation

Téléchargez `ProGrab.exe` depuis la page [Releases](../../releases) et lancez-le. Au premier lancement il télécharge ses composants (~200 Mo, une seule fois).

> **Note SmartScreen** : Windows peut avertir d'un exécutable non signé, c'est normal pour un petit projet indépendant. Cliquez sur *Informations complémentaires* puis *Exécuter quand même*. Le code source est entièrement lisible dans ce dépôt.

### Depuis les sources

```
pip install customtkinter pillow
python prograb.py
```

### Compiler soi-même l'exe

```
pip install pyinstaller customtkinter pillow
pyinstaller --onefile --noconsole --collect-all customtkinter --icon prograb.ico --add-data "prograb.ico;." --name ProGrab prograb.py
```

## ⚠️ Avertissement légal

Télécharger des vidéos depuis YouTube et la plupart des plateformes **viole leurs conditions d'utilisation** et peut enfreindre le droit d'auteur selon le contenu et votre pays. ProGrab est fourni **à des fins personnelles et éducatives uniquement** (par ex. sauvegarder vos propres contenus, accéder hors-ligne à du contenu librement licencié). Vous êtes seul responsable de l'usage que vous en faites. L'auteur n'encourage pas le piratage.

## Prérequis

- Windows 10 / 11

## Licence

MIT — pour l'app elle-même. yt-dlp, ffmpeg et deno appartiennent à leurs projets et licences respectifs.

---

<p align="center">
  Développé par <a href="https://github.com/karkarofff">Karkarofff</a> — jetez aussi un œil à <a href="https://github.com/karkarofff/probox">ProBox</a> et <a href="https://github.com/karkarofff/prokill">ProKill</a>
</p>
