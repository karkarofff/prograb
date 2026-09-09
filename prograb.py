#!/usr/bin/env python3
# ProGrab v0.1 - téléchargeur de vidéos (yt-dlp + interface CustomTkinter)
# Requis : pip install customtkinter pillow
# Exe : pyinstaller --onefile --noconsole --collect-all customtkinter --icon prograb.ico --name ProGrab prograb.py
#
# Au premier lancement, l'app télécharge yt-dlp.exe et ffmpeg dans son
# dossier de données, puis yt-dlp se met à jour tout seul à chaque
# démarrage : l'app reste fonctionnelle même quand YouTube change.

import os
import re
import sys
import json
import time
import zipfile
import threading
import subprocess
import webbrowser
import urllib.request
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    import customtkinter as ctk
except ImportError:
    print("customtkinter manquant. ->  pip install customtkinter pillow")
    sys.exit(1)

APP_NAME = "ProGrab"
APP_VERSION = "0.2.2"
AUTHOR = "Karkarofff"
AUTHOR_URL = "https://github.com/karkarofff"
UPDATE_URL = ("https://raw.githubusercontent.com/karkarofff/prograb/"
              "main/version.json")
RELEASES_URL = "https://github.com/karkarofff/prograb/releases/latest"


def res_path(name):
    base = getattr(sys, "_MEIPASS",
                   os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

# ---------- Palette ----------
BG      = "#141419"
BG2     = "#1d1e25"
BG3     = "#282a33"
FG      = "#eceef2"
FG_DIM  = "#9a9ba6"
ACCENT  = "#ff4d5e"      # rouge ProGrab
ACCENT_H = "#e03848"     # survol
GREEN   = "#4fbf78"

DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                        APP_NAME)
BIN_DIR = os.path.join(DATA_DIR, "bin")
YTDLP = os.path.join(BIN_DIR, "yt-dlp.exe")
FFMPEG = os.path.join(BIN_DIR, "ffmpeg.exe")
DENO = os.path.join(BIN_DIR, "deno.exe")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

YTDLP_URL = ("https://github.com/yt-dlp/yt-dlp/releases/latest/"
             "download/yt-dlp.exe")
# builds ffmpeg maintenus par l'équipe yt-dlp (noms de fichiers stables)
FFMPEG_URL = ("https://github.com/yt-dlp/FFmpeg-Builds/releases/latest/"
              "download/ffmpeg-master-latest-win64-gpl.zip")
# moteur JavaScript requis par yt-dlp pour l'extraction YouTube
DENO_URL = ("https://github.com/denoland/deno/releases/latest/"
            "download/deno-x86_64-pc-windows-msvc.zip")

QUALITIES = ["Max", "1080p", "720p", "480p", "MP3 (audio)"]
MP4 = ["--merge-output-format", "mp4"]
# vcodec^=avc1 = H.264, acodec^=mp4a = AAC : le combo lisible partout.
# YouTube fournit toujours du H.264 jusqu'en 1080p ; au-dela (Max),
# repli sur le meilleur flux disponible remballe en .mp4.
FORMATS = {
    "Max": ["-f", "bv*[vcodec^=avc1]+ba[acodec^=mp4a]/bv*+ba/b"] + MP4,
    "1080p": ["-f", "bv*[vcodec^=avc1][height<=1080]+ba[acodec^=mp4a]/"
                    "bv*[height<=1080]+ba/b[height<=1080]"] + MP4,
    "720p": ["-f", "bv*[vcodec^=avc1][height<=720]+ba[acodec^=mp4a]/"
                   "bv*[height<=720]+ba/b[height<=720]"] + MP4,
    "480p": ["-f", "bv*[vcodec^=avc1][height<=480]+ba[acodec^=mp4a]/"
                   "bv*[height<=480]+ba/b[height<=480]"] + MP4,
    "MP3 (audio)": ["-x", "--audio-format", "mp3"],
}

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def download_file(url, dest, progress_cb=None):
    """Télécharge un fichier avec progression (0.0 -> 1.0)."""
    req = urllib.request.Request(
        url, headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            while True:
                chunk = r.read(1024 * 256)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if progress_cb and total:
                    progress_cb(done / total)


def round_rect(canvas, x1, y1, x2, y2, r, **kw):
    pts = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2,
           x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


class ActionBar(tk.Canvas):
    """Le bouton Télécharger qui devient barre de progression."""
    H, R = 52, 14

    def __init__(self, parent, on_start, on_cancel, on_open):
        super().__init__(parent, height=self.H, bg=BG2,
                         highlightthickness=0)
        self.on_start, self.on_cancel = on_start, on_cancel
        self.on_open = on_open
        self.mode = "idle"          # idle / dl / done / err
        self.pct, self.txt = 0.0, "⬇  Télécharger"
        self.enabled, self.hover = True, False
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.configure(cursor="hand2")

    def _set_hover(self, v):
        self.hover = v
        self._draw()

    def set_enabled(self, v):
        self.enabled = v
        self._draw()

    def set_idle(self):
        self.mode, self.pct, self.txt = "idle", 0, "⬇  Télécharger"
        self._draw()

    def set_progress(self, pct, txt):
        self.mode, self.pct, self.txt = "dl", pct, txt
        self._draw()

    def set_text(self, txt):
        self.txt = txt
        self._draw()

    def set_done(self):
        self.mode, self.pct = "done", 100
        self.txt = "✅ Terminé — clique pour ouvrir le dossier"
        self._draw()

    def set_error(self):
        self.mode, self.pct = "err", 0
        self.txt = "❌ Échec — clique pour réessayer"
        self._draw()

    def _click(self, _):
        if not self.enabled:
            return
        if self.mode in ("idle", "err"):
            self.on_start()
        elif self.mode == "dl":
            self.on_cancel()
        elif self.mode == "done":
            self.on_open()

    def _draw(self):
        self.delete("all")
        w, h = max(self.winfo_width(), 60), self.H
        if self.mode == "idle":
            fill = BG3 if not self.enabled else (
                ACCENT_H if self.hover else ACCENT)
            round_rect(self, 1, 1, w-1, h-1, self.R, fill=fill,
                       outline=fill)
            tcol = "#ffffff" if self.enabled else FG_DIM
        elif self.mode == "dl":
            round_rect(self, 1, 1, w-1, h-1, self.R, fill=BG3,
                       outline=BG3)
            fw = int((w - 2) * min(self.pct, 100) / 100)
            if fw > 6:
                r = min(self.R, fw // 2)
                round_rect(self, 1, 1, 1 + fw, h-1, r, fill=ACCENT,
                           outline=ACCENT)
            self.create_text(w - 22, h // 2, text="✕", fill=FG_DIM,
                             font=("Segoe UI", 12, "bold"))
            tcol = "#ffffff"
        elif self.mode == "done":
            fill = "#5ccb87" if self.hover else GREEN
            round_rect(self, 1, 1, w-1, h-1, self.R, fill=fill,
                       outline=fill)
            tcol = "#0f1512"
        else:
            round_rect(self, 1, 1, w-1, h-1, self.R, fill=BG3,
                       outline=BG3)
            tcol = ACCENT
        self.create_text(w // 2, h // 2, text=self.txt, fill=tcol,
                         font=("Segoe UI", 13, "bold"))


class ProGrab(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title(APP_NAME)
        self.geometry("760x640")
        self.minsize(680, 560)
        self.configure(fg_color=BG)

        cfg = load_config()
        self.out_dir = cfg.get("out_dir") or os.path.join(
            os.path.expanduser("~"), "Downloads")
        q = cfg.get("quality")
        self._saved_quality = q if q in QUALITIES else "1080p"
        self._info = None
        self._proc = None
        self._thumb = None
        self._ready = False

        self._build()
        try:
            self.iconbitmap(res_path("prograb.ico"))
        except Exception:
            pass
        threading.Thread(target=self._setup_tools, daemon=True).start()
        threading.Thread(target=self._check_app_update,
                         daemon=True).start()

    # ================= UI =================
    def _build(self):
        # ---- en-tête ----
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=26, pady=(20, 4))
        ctk.CTkLabel(head, text="⬇", font=("Segoe UI Emoji", 26),
                     text_color=ACCENT).pack(side="left")
        ctk.CTkLabel(head, text=APP_NAME,
                     font=("Segoe UI", 26, "bold")).pack(side="left",
                                                         padx=(10, 6))
        ctk.CTkLabel(head, text=f"v{APP_VERSION}", text_color=FG_DIM,
                     font=("Segoe UI", 12)).pack(side="left", pady=(8, 0))
        ctk.CTkLabel(head, text="Colle un lien YouTube, choisis la "
                                "qualité, télécharge.",
                     text_color=FG_DIM,
                     font=("Segoe UI", 12)).pack(side="right", pady=(8, 0))

        # ---- barre lien ----
        bar = ctk.CTkFrame(self, fg_color=BG2, corner_radius=16)
        bar.pack(fill="x", padx=26, pady=(14, 0))
        self.url_var = tk.StringVar()
        self.url_entry = ctk.CTkEntry(
            bar, textvariable=self.url_var, height=44,
            placeholder_text="https://www.youtube.com/watch?v=...",
            fg_color=BG3, border_width=0, corner_radius=12,
            font=("Segoe UI", 13))
        self.url_entry.pack(side="left", fill="x", expand=True,
                            padx=(14, 8), pady=12)
        self.url_entry.bind("<Return>", lambda e: self.analyse())
        ctk.CTkButton(bar, text="📋", width=44, height=44,
                      corner_radius=12, fg_color=BG3,
                      hover_color="#333540", font=("Segoe UI Emoji", 15),
                      command=self._paste).pack(side="left", padx=(0, 8),
                                                pady=12)
        self.go_btn = ctk.CTkButton(
            bar, text="Analyser", width=120, height=44, corner_radius=12,
            fg_color=ACCENT, hover_color=ACCENT_H,
            font=("Segoe UI", 13, "bold"), command=self.analyse)
        self.go_btn.pack(side="left", padx=(0, 14), pady=12)

        # ---- carte vidéo ----
        self.card = ctk.CTkFrame(self, fg_color=BG2, corner_radius=16)
        self.thumb_lbl = ctk.CTkLabel(self.card, text="")
        self.title_lbl = ctk.CTkLabel(self.card, text="",
                                      font=("Segoe UI", 15, "bold"),
                                      wraplength=380, justify="left",
                                      anchor="w")
        self.meta_lbl = ctk.CTkLabel(self.card, text="",
                                     text_color=FG_DIM,
                                     font=("Segoe UI", 12), anchor="w")

        # ---- options ----
        self.opts = ctk.CTkFrame(self, fg_color="transparent")
        ctk.CTkLabel(self.opts, text="Qualité",
                     font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.quality = ctk.CTkSegmentedButton(
            self.opts, values=QUALITIES, height=38, corner_radius=10,
            fg_color=BG2, selected_color=ACCENT,
            selected_hover_color=ACCENT_H, unselected_color=BG2,
            unselected_hover_color=BG3, font=("Segoe UI", 12),
            command=self._save_quality)
        self.quality.set(self._saved_quality)
        self.quality.pack(fill="x", pady=(6, 12))

        folder_row = ctk.CTkFrame(self.opts, fg_color="transparent")
        folder_row.pack(fill="x")
        ctk.CTkButton(folder_row, text="📁", width=40, height=34,
                      corner_radius=10, fg_color=BG3,
                      hover_color="#333540",
                      command=self._pick_folder).pack(side="left")
        self.folder_lbl = ctk.CTkLabel(folder_row, text=self.out_dir,
                                       text_color=FG_DIM,
                                       font=("Segoe UI", 11), anchor="w")
        self.folder_lbl.pack(side="left", padx=10)

        self.action = ActionBar(
            self.opts, on_start=self.download, on_cancel=self.cancel,
            on_open=lambda: os.startfile(self.out_dir))
        self.action.configure(bg=BG)
        self.action.pack(fill="x", pady=(16, 0))

        # ---- statut / pied ----
        self.status_lbl = ctk.CTkLabel(self, text="", text_color=FG_DIM,
                                       font=("Segoe UI", 12))
        self.status_lbl.pack(side="bottom", pady=(0, 6))
        credit = ctk.CTkLabel(self, text=f"développé par {AUTHOR}",
                              text_color=FG_DIM, font=("Segoe UI", 10),
                              cursor="hand2")
        credit.pack(side="bottom", pady=(0, 2))
        credit.bind("<Button-1>", lambda e: webbrowser.open(AUTHOR_URL))
        credit.bind("<Button-3>",
                    lambda e: threading.Thread(
                        target=self._check_app_update, args=(False,),
                        daemon=True).start())

        # ---- écran de préparation (premier lancement) ----
        self.setup_frame = ctk.CTkFrame(self, fg_color=BG2,
                                        corner_radius=16)
        self.setup_frame.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(self.setup_frame, text="🔧 Préparation...",
                     font=("Segoe UI", 16, "bold")).pack(padx=40,
                                                         pady=(24, 4))
        self.setup_lbl = ctk.CTkLabel(self.setup_frame, text="",
                                      text_color=FG_DIM,
                                      font=("Segoe UI", 12))
        self.setup_lbl.pack(padx=40)
        self.setup_bar = ctk.CTkProgressBar(self.setup_frame, width=320,
                                            height=10, corner_radius=6,
                                            progress_color=ACCENT,
                                            fg_color=BG3)
        self.setup_bar.set(0)
        self.setup_bar.pack(padx=40, pady=(10, 24))

        self._lock_ui(True)

    def _check_app_update(self, silent=True):
        try:
            req = urllib.request.Request(
                UPDATE_URL,
                headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode())
            latest = data.get("version", "0")

            def ver(v):
                return tuple(int(x) for x in v.split("."))
            if ver(latest) > ver(APP_VERSION):
                def notify():
                    self.status_lbl.configure(
                        text=f"🔵 Nouvelle version disponible "
                             f"({latest}) — clique ici pour la "
                             f"télécharger", text_color="#6aa8ff",
                        cursor="hand2")
                    self.status_lbl.bind(
                        "<Button-1>",
                        lambda e: webbrowser.open(
                            data.get("url", RELEASES_URL)))
                self.after(0, notify)
            elif not silent:
                self.after(0, lambda: messagebox.showinfo(
                    APP_NAME, f"Tu as déjà la dernière version "
                              f"({APP_VERSION})."))
        except Exception:
            if not silent:
                self.after(0, lambda: messagebox.showwarning(
                    APP_NAME, "Impossible de vérifier les mises à "
                              "jour (pas de connexion ?)."))

    def _lock_ui(self, locked):
        state = "disabled" if locked else "normal"
        self.go_btn.configure(state=state)
        self.action.set_enabled(not locked)

    # ================= outils (yt-dlp / ffmpeg) =================
    def _setup_status(self, txt, frac=None):
        def apply():
            self.setup_lbl.configure(text=txt)
            if frac is not None:
                self.setup_bar.set(frac)
        self.after(0, apply)

    def _setup_tools(self):
        try:
            os.makedirs(BIN_DIR, exist_ok=True)
            if not os.path.exists(YTDLP):
                self._setup_status("Téléchargement de yt-dlp "
                                   "(moteur de téléchargement)...", 0)
                download_file(YTDLP_URL, YTDLP,
                              lambda f: self._setup_status(
                                  "Téléchargement de yt-dlp...", f * 0.3))
            if not os.path.exists(FFMPEG):
                self._setup_status("Téléchargement de ffmpeg "
                                   "(conversion audio/vidéo)...", 0.3)
                zpath = os.path.join(BIN_DIR, "ffmpeg.zip")
                download_file(FFMPEG_URL, zpath,
                              lambda f: self._setup_status(
                                  "Téléchargement de ffmpeg "
                                  "(~150 Mo, une seule fois)...",
                                  0.3 + f * 0.6))
                self._setup_status("Installation de ffmpeg...", 0.92)
                with zipfile.ZipFile(zpath) as z:
                    for name in z.namelist():
                        base = os.path.basename(name)
                        if base in ("ffmpeg.exe", "ffprobe.exe"):
                            with z.open(name) as src, open(
                                    os.path.join(BIN_DIR, base),
                                    "wb") as dst:
                                dst.write(src.read())
                os.remove(zpath)
            if not os.path.exists(DENO):
                self._setup_status("Téléchargement du moteur JavaScript "
                                   "(deno)...", 0.9)
                zpath = os.path.join(BIN_DIR, "deno.zip")
                download_file(DENO_URL, zpath,
                              lambda f: self._setup_status(
                                  "Téléchargement du moteur JavaScript "
                                  "(deno)...", 0.9 + f * 0.06))
                with zipfile.ZipFile(zpath) as z:
                    for name in z.namelist():
                        if os.path.basename(name) == "deno.exe":
                            with z.open(name) as s, open(DENO, "wb") as d:
                                d.write(s.read())
                os.remove(zpath)
            # mise à jour silencieuse de yt-dlp (le cœur de la fiabilité)
            self._setup_status("Vérification des mises à jour "
                               "de yt-dlp...", 0.97)
            try:
                subprocess.run([YTDLP, "-U"], capture_output=True,
                               timeout=90, creationflags=NO_WINDOW)
            except Exception:
                pass
            self._ready = True
            self.after(0, lambda: (self.setup_frame.place_forget(),
                                   self._lock_ui(False),
                                   self.status_lbl.configure(
                                       text="Prêt. Colle un lien pour "
                                            "commencer.")))
        except Exception as e:
            self._setup_status(f"Échec de la préparation : {e}\n"
                               "Vérifie ta connexion et relance l'app.", 0)

    def _ytdlp_base(self):
        args = [YTDLP]
        if os.path.exists(DENO):
            args += ["--js-runtimes", f"deno:{DENO}"]
        return args

    # ================= analyse =================
    def _paste(self):
        try:
            self.url_var.set(self.clipboard_get().strip())
        except tk.TclError:
            pass

    def analyse(self):
        url = self.url_var.get().strip()
        if not url or not self._ready:
            return
        self.go_btn.configure(state="disabled", text="...")
        self.status_lbl.configure(text="Analyse de la vidéo...")

        def worker():
            try:
                r = subprocess.run(
                    self._ytdlp_base() + ["-J", "--no-playlist", url],
                    capture_output=True, text=True, timeout=60,
                    creationflags=NO_WINDOW, encoding="utf-8",
                    errors="replace")
                info = json.loads(r.stdout)
            except Exception:
                self.after(0, lambda: (
                    self.go_btn.configure(state="normal", text="Analyser"),
                    self.status_lbl.configure(
                        text="Impossible d'analyser ce lien. Vérifie "
                             "l'URL.")))
                return
            thumb_img = None
            try:
                from PIL import Image
                import io
                req = urllib.request.Request(
                    info.get("thumbnail"),
                    headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    raw = resp.read()
                img = Image.open(io.BytesIO(raw))
                img.thumbnail((300, 170))
                thumb_img = ctk.CTkImage(light_image=img, dark_image=img,
                                         size=img.size)
            except Exception:
                pass
            self.after(0, lambda: self._show_info(info, thumb_img))
        threading.Thread(target=worker, daemon=True).start()

    def _show_info(self, info, thumb_img):
        self._info = info
        self.go_btn.configure(state="normal", text="Analyser")
        if self._proc is None:
            self.action.set_idle()
        dur = info.get("duration") or 0
        m, s = divmod(int(dur), 60)
        h, m = divmod(m, 60)
        dur_txt = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
        views = info.get("view_count")
        meta = f'{info.get("uploader", "?")}  ·  {dur_txt}'
        if views:
            meta += f'  ·  {views:,} vues'.replace(",", " ")

        self.card.pack(fill="x", padx=26, pady=(14, 0))
        if thumb_img:
            self._thumb = thumb_img
            self.thumb_lbl.configure(image=thumb_img, text="")
        else:
            self.thumb_lbl.configure(image=None, text="🎬",
                                     font=("Segoe UI Emoji", 48))
        self.thumb_lbl.pack(side="left", padx=16, pady=16)
        txtcol = ctk.CTkFrame(self.card, fg_color="transparent")
        # (re)packer proprement la colonne texte
        for w in self.card.winfo_children():
            if isinstance(w, ctk.CTkFrame) and w not in (self.thumb_lbl,):
                w.destroy()
        col = ctk.CTkFrame(self.card, fg_color="transparent")
        col.pack(side="left", fill="both", expand=True, padx=(0, 16),
                 pady=16)
        self.title_lbl = ctk.CTkLabel(col, text=info.get("title", "?"),
                                      font=("Segoe UI", 15, "bold"),
                                      wraplength=380, justify="left",
                                      anchor="w")
        self.title_lbl.pack(anchor="w")
        self.meta_lbl = ctk.CTkLabel(col, text=meta, text_color=FG_DIM,
                                     font=("Segoe UI", 12), anchor="w")
        self.meta_lbl.pack(anchor="w", pady=(6, 0))

        self.opts.pack(fill="x", padx=26, pady=(14, 0))
        self.status_lbl.configure(text="")

    # ================= téléchargement =================
    def _save_quality(self, value):
        cfg = load_config()
        cfg["quality"] = value
        save_config(cfg)

    def _pick_folder(self):
        folder = filedialog.askdirectory(initialdir=self.out_dir)
        if folder:
            self.out_dir = folder
            self.folder_lbl.configure(text=folder)
            cfg = load_config()
            cfg["out_dir"] = folder
            save_config(cfg)

    def download(self):
        try:
            self._download()
        except Exception:
            messagebox.showerror(
                APP_NAME, "Erreur interne :\n\n"
                + traceback.format_exc(limit=5))
            self.action.set_error()

    def _download(self):
        if not self._info or self._proc:
            return
        url = self.url_var.get().strip()
        q = self.quality.get()
        cmd = self._ytdlp_base() + [
               "--no-playlist", "--windows-filenames",
               "--force-overwrites",
               "--ffmpeg-location", BIN_DIR, "--newline", "--progress",
               "--progress-template",
               "PG|%(progress._percent_str)s"
               "|%(progress._total_bytes_str)s"
               "|%(progress._total_bytes_estimate_str)s"
               "|%(progress._speed_str)s|%(progress._eta_str)s",
               "-o", os.path.join(self.out_dir, "%(title)s.%(ext)s")]
        cmd += FORMATS[q] + [url]

        self.action.set_progress(0, "Démarrage...")

        def worker():
            def clean(v):
                v = v.strip()
                return "" if v in ("NA", "N/A", "Unknown", "---") else v
            legacy = re.compile(
                r"(\d+(?:\.\d+)?)%\s+of\s+~?\s*([\d.]+\w+)"
                r"(?:\s+at\s+([\d.]+\w+/s))?(?:\s+ETA\s+([\d:]+))?")
            log = open(os.path.join(DATA_DIR, "last.log"), "w",
                       encoding="utf-8", errors="replace")
            try:
                env = os.environ.copy()
                env["PYTHONUNBUFFERED"] = "1"
                self._proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, text=True, bufsize=1,
                    creationflags=NO_WINDOW, encoding="utf-8",
                    errors="replace", env=env)
                for line in iter(self._proc.stdout.readline, ""):
                    log.write(line)
                    line = line.strip("\r\n")
                    if "PG|" in line:
                        line = line[line.index("PG|"):]
                        parts = line.strip().split("|")
                        if len(parts) < 6:
                            continue
                        try:
                            pct = float(parts[1].strip().rstrip("%"))
                        except ValueError:
                            continue
                        txt = f"{pct:.0f}%"
                        total = clean(parts[2]) or clean(parts[3])
                        if total:
                            txt += f"  ·  {total}"
                        if clean(parts[4]):
                            txt += f"  ·  {clean(parts[4])}"
                        if clean(parts[5]):
                            txt += f"  ·  reste {clean(parts[5])}"
                        self.after(0, lambda p=pct, t=txt:
                                   self.action.set_progress(p, t))
                    elif "[Merger]" in line or "[ExtractAudio]" in line:
                        self.after(0, lambda: self.action.set_text(
                            "Finalisation (fusion/conversion)..."))
                    else:
                        m = legacy.search(line)
                        if m:
                            pct = float(m.group(1))
                            txt = f"{pct:.0f}%  ·  {m.group(2)}"
                            if m.group(3):
                                txt += f"  ·  {m.group(3)}"
                            if m.group(4):
                                txt += f"  ·  reste {m.group(4)}"
                            self.after(0, lambda p=pct, t=txt:
                                       self.action.set_progress(p, t))
                code = self._proc.wait()
            except Exception:
                try:
                    log.write("\n--- ERREUR INTERNE ---\n")
                    log.write(traceback.format_exc())
                except OSError:
                    pass
                code = -1
            finally:
                try:
                    log.close()
                except OSError:
                    pass
            cancelled = self._proc is None
            self._proc = None
            def done():
                if cancelled:
                    self.action.set_idle()
                    self.status_lbl.configure(text="Annulé.")
                elif code == 0:
                    self.action.set_done()
                    self.status_lbl.configure(text="")
                    try:
                        os.startfile(self.out_dir)
                    except OSError:
                        pass
                else:
                    self.action.set_error()
                    self.status_lbl.configure(
                        text="Réessaie, ou relance l'app (yt-dlp se "
                             "mettra à jour tout seul).")
            self.after(0, done)
        threading.Thread(target=worker, daemon=True).start()

    def cancel(self):
        proc, self._proc = self._proc, None
        if proc:
            try:
                proc.kill()
            except OSError:
                pass


if __name__ == "__main__":
    ProGrab().mainloop()