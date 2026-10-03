"""Generate a pixel-controlled Green Smile radiographic report locally."""

from __future__ import annotations

import base64
import os
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

CANVAS_WIDTH = 1672
CANVAS_HEIGHT = 958
SUPPORTED = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
SLOTS = {
    1: (60, 143, 280, 180),
    2: (60, 339, 280, 180),
    8: (60, 535, 280, 180),
    9: (60, 727, 280, 180),
    3: (429, 202, 185, 270),
    4: (638, 202, 185, 270),
    15: (847, 202, 185, 270),
    5: (1056, 202, 185, 270),
    10: (429, 565, 185, 270),
    11: (638, 565, 185, 270),
    16: (847, 565, 185, 270),
    12: (1056, 565, 185, 270),
    6: (1332, 143, 280, 180),
    7: (1332, 339, 280, 180),
    13: (1332, 535, 280, 180),
    14: (1332, 727, 280, 180),
}


def find_images(directory: Path) -> dict[int, Path]:
    """Map two-digit filename prefixes to the 16 fixed report slots."""

    mapped: dict[int, Path] = {}
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED:
            continue
        prefix = path.name[:2]
        if not prefix.isascii() or not prefix.isdigit():
            continue
        slot = int(prefix)
        if slot not in SLOTS:
            continue
        if slot in mapped:
            raise ValueError(f"mais de uma imagem usa a posicao {slot:02d}")
        with Image.open(path) as image:
            image.verify()
        mapped[slot] = path
    missing = sorted(set(SLOTS) - set(mapped))
    if missing:
        numbers = ", ".join(f"{slot:02d}" for slot in missing)
        raise ValueError(f"faltam imagens para as posicoes: {numbers}")
    return mapped


def data_uri(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def build_html(images: dict[int, Path], logo_path: Path) -> str:
    frames = []
    for slot, (left, top, width, height) in SLOTS.items():
        frames.append(
            f'<div class="film" style="left:{left}px;top:{top}px;width:{width}px;'
            f'height:{height}px"><img src="{data_uri(images[slot])}" alt="{slot:02d}"></div>'
        )
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><style>
@page {{ size: {CANVAS_WIDTH}px {CANVAS_HEIGHT}px; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin:0; width:{CANVAS_WIDTH}px; height:{CANVAS_HEIGHT}px; overflow:hidden; }}
body {{ background:#000; font-family:Arial,Helvetica,sans-serif; }}
.mount {{ position:relative; width:{CANVAS_WIDTH}px; height:{CANVAS_HEIGHT}px; background:#000; }}
.header {{ position:absolute; inset:0 0 auto 0; height:125px; overflow:hidden;
  background:linear-gradient(90deg,#04362a 0 31%,#021f19 31% 100%);
  border-bottom:2px solid #f16f22; }}
.logo {{ position:absolute; left:60px; top:7px; width:445px; height:108px; object-fit:contain; }}
.divider {{ position:absolute; left:510px; top:24px; width:3px; height:75px; background:#f16f22; }}
.patient {{ position:absolute; left:548px; top:18px; color:#fff; font-size:24px;
  line-height:1.28; font-weight:700; white-space:nowrap; }}
.patient strong {{ color:#f16f22; }}
.dots {{ position:absolute; right:118px; top:9px; width:300px; height:92px;
  background:radial-gradient(circle,#f16f22 0 2.5px,transparent 3px) 0 0/15px 15px;
  transform:skewX(-18deg); opacity:.95; mask-image:linear-gradient(90deg,transparent,#000); }}
.wave {{ position:absolute; right:-15px; top:72px; width:420px; height:70px;
  border-top:6px solid #f16f22; border-radius:50%; transform:rotate(-4deg);
  box-shadow:0 9px 0 #064c39,0 18px 0 #043c30,0 27px 0 #032f27; }}
.film {{ position:absolute; overflow:hidden; border:1.5px solid #ddd;
  border-radius:25px; background:#000; }}
.film img {{ width:100%; height:100%; display:block; object-fit:cover;
  object-position:center; filter:grayscale(1); }}
</style></head><body><main class="mount">
<header class="header"><img class="logo" src="{data_uri(logo_path)}" alt="Green Smile">
<div class="divider"></div><div class="patient">
Paciente: <strong>Douglas do Nascimento Castilho</strong><br>
Exame: <strong>Série periapical</strong><br>Data: <strong>01/10/2026</strong></div>
<div class="dots"></div><div class="wave"></div></header>
{''.join(frames)}
</main></body></html>"""


def generate(project: Path) -> Path:
    images = find_images(project / "xray")
    logo = project / "assets" / "green_smile_logo_header.png"
    if not logo.is_file():
        raise FileNotFoundError(f"logo nao encontrado: {logo}")
    sao_paulo = timezone(timedelta(hours=-3))
    stamp = datetime.now(sao_paulo).strftime("%Y-%m-%d_%H-%M-%S")
    output = project / "relatorio" / f"Douglas_do_Nascimento_Castilho_{stamp}"
    output.mkdir(parents=True)
    html_path = output / "montagem.html"
    html_path.write_text(build_html(images, logo), encoding="utf-8")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": CANVAS_WIDTH, "height": CANVAS_HEIGHT}, device_scale_factor=1
        )
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.screenshot(path=str(output / "periapical_series_preview.png"), full_page=True)
        page.pdf(
            path=str(output / "periapical_series.pdf"),
            width=f"{CANVAS_WIDTH}px",
            height=f"{CANVAS_HEIGHT}px",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        browser.close()
    (output / "report.txt").write_text(
        "Green Smile - Serie periapical\n"
        "Paciente: Douglas do Nascimento Castilho\n"
        "Data: 01/10/2026\n"
        "Imagens: 16\n"
        "Arquivos originais: nao modificados\n",
        encoding="utf-8",
    )
    return output


def show_message(message: str, *, error: bool = False) -> None:
    if os.environ.get("XRAY_MOUTH_NO_DIALOG") == "1":
        return
    try:
        from tkinter import Tk, messagebox

        root = Tk()
        root.withdraw()
        (messagebox.showerror if error else messagebox.showinfo)(
            "XRay Mouth HTML Pro", message, parent=root
        )
        root.destroy()
    except Exception:
        pass


def main() -> int:
    try:
        output = generate(Path(__file__).resolve().parent)
        pdf = output / "periapical_series.pdf"
        print(f"Relatorio criado: {output}")
        print(f"PDF: {pdf}")
        if os.name == "nt" and os.environ.get("XRAY_MOUTH_NO_DIALOG") != "1":
            os.startfile(pdf)  # type: ignore[attr-defined]
        show_message(f"Relatorio concluido.\n\n{output}")
        return 0
    except Exception as exc:
        traceback.print_exc()
        show_message(str(exc), error=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

