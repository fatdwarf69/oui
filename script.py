import os
import sys
import shutil
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import cv2
from PIL import Image
import pytesseract

# ==================================================================
# CONFIGURATION
# ==================================================================
VIDEOS_DIR = Path(r"E:\videos\full")
OUTPUT_DIR = Path(r"E:\videos\cut")
FFMPEG     = Path(r"E:\videos\ffmpeg\bin\ffmpeg.exe")
FFPROBE    = Path(r"E:\videos\ffmpeg\bin\ffprobe.exe")

# Moteur Tesseract (installation standard)
TESSERACT_EXE = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA_DIR  = Path(r"C:\Program Files\Tesseract-OCR\tessdata")

# Paramètres détection
SAMPLE_FPS    = 1      # frames analysées par seconde (1 = bon compromis)
MIN_BUY_HITS  = 2      # nb d'armes reconnues pour valider "boutique"
OCR_WORKERS   = 4      # threads OCR (monte à 8 si CPU costaud)
DRY_RUN       = False  # True = affiche les segments sans encoder


# ==================================================================
# SETUP
# ==================================================================
pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_EXE)
os.environ["TESSDATA_PREFIX"] = str(TESSDATA_DIR)


# ==================================================================
# INTERACTIF
# ==================================================================
def pick_video():
    if not VIDEOS_DIR.exists():
        print(f"❌ {VIDEOS_DIR} introuvable")
        sys.exit(1)
    vids = sorted(f for f in VIDEOS_DIR.iterdir()
                  if f.suffix.lower() in (".mp4", ".mkv", ".mov", ".avi", ".webm"))
    if not vids:
        print(f"❌ Aucune vidéo dans {VIDEOS_DIR}")
        sys.exit(1)
    print("\nVidéos disponibles :")
    for i, v in enumerate(vids, 1):
        print(f"  [{i}] {v.name}")
    while True:
        try:
            return vids[int(input("\nNuméro : ")) - 1]
        except (ValueError, IndexError):
            print("Choix invalide")


OUTPUT_EXTS = {".mp4", ".mkv", ".mov"}   # formats supportés par libx264+aac


def pick_output(src):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    default_ext = src.suffix.lower() if src.suffix.lower() in OUTPUT_EXTS else ".mp4"
    default = f"{src.stem}_cut{default_ext}"

    while True:
        raw = input(f"\nNom de sortie (défaut: {default}) : ").strip()
        if not raw:
            name = default
        else:
            p = Path(raw)
            if p.suffix.lower() in OUTPUT_EXTS:
                name = raw                             # extension déjà valide
            elif p.suffix == "":                       # pas d'extension
                name = raw + default_ext               # on ajoute celle de l'entrée
            else:
                print(f"⚠️  Extension '{p.suffix}' non supportée. "
                      f"Utilise : {', '.join(sorted(OUTPUT_EXTS))}")
                continue

        out = OUTPUT_DIR / name
        if out.exists() and input(f"{out} existe déjà, écraser ? (o/n) : ").lower() != "o":
            continue
        return out


# ==================================================================
# EXTRACTION + OCR
# ==================================================================
def extract_frames(video, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Extraction à {SAMPLE_FPS} fps...")
    subprocess.run(
        [str(FFMPEG), "-y", "-i", str(video),
         "-vf", f"fps={SAMPLE_FPS}", "-q:v", "3",
         str(out_dir / "f_%06d.jpg")],
        check=True, capture_output=True,
    )


# ==================================================================
# MAIN
# ==================================================================

video = pick_video()

frames_dir = OUTPUT_DIR / f"{video.stem}_frames"

if frames_dir.exists():
    shutil.rmtree(frames_dir)

frames_dir.mkdir(parents=True, exist_ok=True)

print(f"\n🎥 Vidéo sélectionnée : {video.name}")
print(f"📁 Dossier de frames : {frames_dir}")

extract_frames(video, frames_dir)

print("\n✅ Extraction terminée !")