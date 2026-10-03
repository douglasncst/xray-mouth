"""Generate the final Green Smile 14-film radiographic report locally."""

from __future__ import annotations

import base64
import html
import io
import os
import re
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageOps
from playwright.sync_api import sync_playwright

CANVAS_WIDTH = 1672
CANVAS_HEIGHT = 941
DOCTOR_NAME = "Victor Greenhalgh"
SUPPORTED = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}

# Geometry measured from the approved final Green Smile reference.
SLOTS = {
    1: (174, 145, 240, 177),
    6: (174, 336, 240, 180),
    7: (174, 531, 240, 179),
    10: (174, 724, 240, 176),
    2: (497, 261, 188, 240),
    3: (734, 261, 188, 242),
    4: (974, 261, 187, 242),
    11: (496, 591, 189, 242),
    12: (734, 591, 188, 242),
    13: (974, 591, 186, 242),
    5: (1191, 145, 243, 177),
    8: (1192, 336, 242, 180),
    9: (1193, 531, 241, 179),
    14: (1192, 724, 242, 177),
}


def _contains_supported_images(directory: Path) -> bool:
    return any(path.is_file() and path.suffix.lower() in SUPPORTED for path in directory.iterdir())


def locate_exam(xray_root: Path) -> tuple[Path, str]:
    """Locate one patient exam and infer the patient name from its folder name."""
    if not xray_root.is_dir():
        raise FileNotFoundError(f"pasta de entrada nao encontrada: {xray_root}")

    patient_dirs = [
        path
        for path in sorted(xray_root.iterdir(), key=lambda p: p.name.casefold())
        if path.is_dir() and not path.name.startswith(".") and _contains_supported_images(path)
    ]
    direct_images = _contains_supported_images(xray_root)

    if patient_dirs and direct_images:
        raise ValueError(
            "ha imagens soltas em xray e tambem uma pasta de paciente; "
            "deixe apenas uma forma de entrada"
        )
    if len(patient_dirs) > 1:
        names = ", ".join(path.name for path in patient_dirs)
        raise ValueError(f"ha mais de uma pasta de paciente em xray: {names}")
    if patient_dirs:
        exam_dir = patient_dirs[0]
        patient_name = re.sub(r"\s+", " ", exam_dir.name.replace("_", " ")).strip()
        if not patient_name:
            raise ValueError("o nome da pasta do paciente esta vazio")
        return exam_dir, patient_name
    if direct_images:
        patient_name = os.environ.get("XRAY_PATIENTE", "").strip()
        if not patient_name:
            raise ValueError(
                "as 14 imagens estao soltas em xray. Crie xray/Nome do Paciente/ "
                "e mova as imagens para essa pasta, ou defina XRAY_PATIENTE"
            )
        return xray_root, patient_name
    raise ValueError(
        "nenhum exame encontrado. Crie xray/Nome do Paciente/ e coloque as 14 imagens nela"
    )


def find_images(directory: Path) -> dict[int, Path]:
    """Map two-digit filename prefixes to the 14 fixed report slots."""
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


def data_uri_file(path: Path) -> str:
    suffix = path.suffix.lower()
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".bmp": "image/bmp",
    }.get(suffix)
    if mime is not None:
        return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"

    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=True)
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('ascii')}"


def header_svg() -> str:
    """Return the approved dark-green/orange Green Smile header artwork."""
    dots = []
    for row in range(7):
        for col in range(14):
            x = 1215 + col * 23 + row * 7
            y = 8 + row * 14 + (col % 2) * 2
            r = max(1.2, 4.6 - row * 0.42 - col * 0.05)
            dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"/>')
    dot_markup = "".join(dots)
    return f'''<svg class="header-art" viewBox="0 0 1672 136" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
<defs>
  <linearGradient id="g" x1="0" x2="1"><stop stop-color="#00130f"/><stop offset=".36" stop-color="#06392e"/><stop offset=".62" stop-color="#00120f"/><stop offset="1" stop-color="#06382f"/></linearGradient>
  <linearGradient id="line" x1="0" x2="1"><stop stop-color="#ff5b00"/><stop offset=".31" stop-color="#ff5b00"/><stop offset=".41" stop-color="#007a5d"/><stop offset=".55" stop-color="#ff5b00"/><stop offset="1" stop-color="#ff5b00"/></linearGradient>
</defs>
<rect width="1672" height="136" fill="url(#g)"/>
<path d="M0 72 C55 105 105 123 188 130 C260 135 330 133 430 133 C560 133 670 132 760 132 C970 132 1130 132 1250 123 C1380 116 1490 93 1672 97 L1672 136 L0 136 Z" fill="#00150f" opacity=".92"/>
<path d="M0 72 C55 106 110 124 195 130 C325 138 525 132 650 132 C765 132 800 132 910 132 C1120 132 1240 132 1340 119 C1460 103 1570 95 1672 98" fill="none" stroke="url(#line)" stroke-width="4"/>
<path d="M1518 38 C1530 19 1541 58 1554 38 S1579 18 1591 38 S1616 58 1628 38 S1653 18 1668 36" fill="none" stroke="#ff5b00" stroke-width="7" stroke-linecap="round"/>
<g fill="#ff5b00" opacity=".95">{dot_markup}</g>
<path d="M0 28 C35 42 62 53 83 69" fill="none" stroke="#315f3d" stroke-width="2" opacity=".65"/>
<path d="M0 36 C35 50 58 61 78 74" fill="none" stroke="#8a6f00" stroke-width="2" opacity=".55"/>
</svg>'''


def build_html(
    images: dict[int, Path], logo_path: Path, patient_name: str, report_date: str
) -> str:
    frames = []
    side_slots = {1, 5, 6, 7, 8, 9, 10, 14}
    for slot, (left, top, width, height) in SLOTS.items():
        radius = 31 if slot in side_slots else 28
        frames.append(
            f'<div class="film" style="left:{left}px;top:{top}px;width:{width}px;'
            f'height:{height}px;border-radius:{radius}px">'
            f'<img src="{data_uri_file(images[slot])}" alt="{slot:02d}"></div>'
        )

    patient = html.escape(patient_name)
    doctor = html.escape(DOCTOR_NAME)
    date = html.escape(report_date)
    return f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><style>
@page {{ size: {CANVAS_WIDTH}px {CANVAS_HEIGHT}px; margin: 0; }}
* {{ box-sizing: border-box; }}
html,body {{ margin:0;width:{CANVAS_WIDTH}px;height:{CANVAS_HEIGHT}px;overflow:hidden; }}
body {{ background:#000;font-family:Arial,Helvetica,sans-serif; }}
.mount {{ position:relative;width:{CANVAS_WIDTH}px;height:{CANVAS_HEIGHT}px;background:#000;overflow:hidden; }}
.header-art {{ position:absolute;left:0;top:0;width:1672px;height:136px;display:block; }}
.logo {{ position:absolute;left:276px;top:6px;width:208px;height:132px;object-fit:contain; }}
.divider {{ position:absolute;left:532px;top:26px;width:4px;height:84px;border-radius:3px;background:#ff5a00; }}
.patient {{ position:absolute;left:580px;top:22px;color:#fff;font-size:22px;line-height:1.34;font-weight:700;letter-spacing:-.25px;white-space:nowrap;text-shadow:0 0 1px rgba(0,0,0,.32); }}
.patient .value {{ color:#ff5a00; }}
.film {{ position:absolute;overflow:hidden;background:#050505;box-shadow:inset 0 0 0 1px rgba(255,255,255,.12); }}
.film img {{ width:100%;height:100%;display:block;object-fit:cover;object-position:center;filter:grayscale(1); }}
</style></head><body><main class="mount">
{header_svg()}
<img class="logo" src="{data_uri_file(logo_path)}" alt="Green Smile Clínica Odontológica">
<div class="divider"></div>
<div class="patient"><div>Paciente: <span class="value">{patient}</span></div><div>Data: <span class="value">{date}</span></div><div>Dr: <span class="value">{doctor}</span></div></div>
{''.join(frames)}
</main></body></html>'''


def _safe_name(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value).strip(" .")
    return cleaned or "Paciente"


def generate(project: Path) -> Path:
    exam_dir, patient_name = locate_exam(project / "xray")
    images = find_images(exam_dir)
    logo = project / "assets" / "green_smile_logo_header.png"
    if not logo.is_file():
        raise FileNotFoundError(f"logo nao encontrado: {logo}")

    sao_paulo = timezone(timedelta(hours=-3))
    now = datetime.now(sao_paulo)
    report_date = now.strftime("%d/%m/%Y")
    stamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    output = project / "relatorio" / f"{_safe_name(patient_name)}_{stamp}"
    output.mkdir(parents=True)
    html_path = output / "montagem.html"
    html_path.write_text(build_html(images, logo, patient_name, report_date), encoding="utf-8")

    with sync_playwright() as playwright:
        launch_kwargs: dict[str, object] = {"headless": True}
        custom_chromium = os.environ.get("XRAY_MOUTH_CHROMIUM")
        if custom_chromium:
            launch_kwargs["executable_path"] = custom_chromium
        browser = playwright.chromium.launch(**launch_kwargs)
        page = browser.new_page(
            viewport={"width": CANVAS_WIDTH, "height": CANVAS_HEIGHT}, device_scale_factor=1
        )
        page.set_content(html_path.read_text(encoding="utf-8"), wait_until="load")
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
        f"Paciente: {patient_name}\n"
        f"Data: {report_date}\n"
        f"Dr: {DOCTOR_NAME}\n"
        "Imagens: 14\n"
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
