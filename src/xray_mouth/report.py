"""Generate a pixel-controlled Green Smile radiographic report locally."""

from __future__ import annotations

import base64
import html
import os
import re
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

CANVAS_WIDTH = 1672
CANVAS_HEIGHT = 941
SUPPORTED = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}

# Geometry reproduced from the new 14-film clinical reference layout.
# Patient data from the reference image is intentionally not embedded in the project.
SLOTS = {
    # Patient-right side: four landscape films.
    1: (174, 145, 240, 176),
    2: (174, 337, 240, 178),
    8: (174, 532, 240, 178),
    9: (174, 725, 240, 175),
    # Maxillary anterior region: three portrait films.
    3: (498, 262, 186, 241),
    4: (735, 262, 186, 241),
    5: (975, 262, 185, 241),
    # Mandibular anterior region: three portrait films.
    10: (498, 591, 186, 241),
    11: (735, 591, 186, 241),
    12: (975, 591, 185, 241),
    # Patient-left side: four landscape films.
    6: (1192, 145, 242, 176),
    7: (1192, 337, 242, 178),
    13: (1192, 532, 242, 178),
    14: (1192, 725, 242, 175),
}


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


def data_uri(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def build_html(
    images: dict[int, Path], logo_path: Path, patient_name: str, exam_date: str
) -> str:
    frames = []
    for slot, (left, top, width, height) in SLOTS.items():
        frames.append(
            f'<div class="film" style="left:{left}px;top:{top}px;width:{width}px;'
            f'height:{height}px"><img src="{data_uri(images[slot])}" alt="{slot:02d}"></div>'
        )
    patient_label = html.escape(patient_name)
    date_label = html.escape(exam_date)
    doctor_label = html.escape(os.environ.get("XRAY_MOUTH_DOCTOR", "Victor Greenhalgh"))
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><style>
@page {{ size: {CANVAS_WIDTH}px {CANVAS_HEIGHT}px; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin:0; width:{CANVAS_WIDTH}px; height:{CANVAS_HEIGHT}px; overflow:hidden; }}
body {{ background:#000; font-family:Arial,Helvetica,sans-serif; }}
.mount {{ position:relative; width:{CANVAS_WIDTH}px; height:{CANVAS_HEIGHT}px; background:#000; }}

.header {{ position:absolute; left:0; top:0; height:138px; width:{CANVAS_WIDTH}px; }}
.logo {{ position:absolute; left:0; top:0; width:{CANVAS_WIDTH}px; height:138px; }}
.patient {{ position:absolute; left:580px; top:23px; color:#fff; font-size:24px;
  line-height:29px; font-weight:700; white-space:nowrap; }}
.patient strong {{ font-weight:700; color:#ff6200; }}

.film {{ position:absolute; overflow:hidden; border-radius:42px; background:#000; }}
.film img {{ width:100%; height:100%; display:block; object-fit:cover;
  object-position:center; filter:grayscale(1); }}
</style></head><body><main class="mount">
<header class="header"><img class="logo" src="{data_uri(logo_path)}" alt="Green Smile">
<div class="patient">
Paciente: <strong>{patient_label}</strong><br>
Data: <strong>{date_label}</strong><br>
Dr: <strong>{doctor_label}</strong>
</div></header>
{''.join(frames)}
</main></body></html>"""


def patient_directories(xray_root: Path) -> list[Path]:
    """Return the immediate patient directories in a stable order."""

    if not xray_root.is_dir():
        raise FileNotFoundError(f"pasta de entrada nao encontrada: {xray_root}")
    directories = sorted(
        (path for path in xray_root.iterdir() if path.is_dir()),
        key=lambda path: path.name.casefold(),
    )
    if not directories:
        raise ValueError(f"nenhuma pasta de paciente encontrada em: {xray_root}")
    return directories


def safe_output_name(patient_name: str) -> str:
    """Create a filesystem-safe name while preserving the patient's display name."""

    safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", patient_name).strip(" .")
    return safe_name or "Paciente"


def generate_patient(project: Path, patient_directory: Path) -> Path:
    patient_name = patient_directory.name
    images = find_images(patient_directory)
    logo = Path(__file__).resolve().parent / "assets" / "green_smile_reference_header.png"
    if not logo.is_file():
        # Editable installations keep artwork in the repository's assets folder.
        logo = Path(__file__).resolve().parents[2] / "assets" / "green_smile_reference_header.png"
    if not logo.is_file():
        raise FileNotFoundError(f"logo nao encontrado: {logo}")
    sao_paulo = timezone(timedelta(hours=-3))
    generated_at = datetime.now(sao_paulo)
    stamp = generated_at.strftime("%Y-%m-%d_%H-%M-%S")
    exam_date = generated_at.strftime("%d/%m/%Y")
    output = project / "relatorio" / f"{safe_output_name(patient_name)}_{stamp}"
    output.mkdir(parents=True)
    html_path = output / "montagem.html"
    html_path.write_text(
        build_html(images, logo, patient_name, exam_date), encoding="utf-8"
    )
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
        f"Paciente: {patient_name}\n"
        f"Data: {exam_date}\n"
        "Imagens: 14\n"
        "Arquivos originais: nao modificados\n",
        encoding="utf-8",
    )
    return output


def generate(project: Path) -> list[Path]:
    """Generate one report for every immediate patient directory under xray."""

    outputs: list[Path] = []
    failures: list[str] = []
    for patient_directory in patient_directories(project / "xray"):
        try:
            outputs.append(generate_patient(project, patient_directory))
        except Exception as exc:
            failures.append(f"{patient_directory.name}: {exc}")
    if failures:
        details = "\n".join(f"- {failure}" for failure in failures)
        raise RuntimeError(f"nao foi possivel gerar todos os relatorios:\n{details}")
    return outputs


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


def main(*, project: Path | None = None, open_pdf: bool = True) -> int:
    try:
        outputs = generate(project if project is not None else Path.cwd())
        for output in outputs:
            pdf = output / "periapical_series.pdf"
            print(f"Relatorio criado: {output}")
            print(f"PDF: {pdf}")
            if open_pdf and os.name == "nt" and os.environ.get("XRAY_MOUTH_NO_DIALOG") != "1":
                os.startfile(pdf)  # type: ignore[attr-defined]
        if open_pdf:
            show_message(f"Relatorios concluidos: {len(outputs)}")
        return 0
    except Exception as exc:
        traceback.print_exc()
        if open_pdf:
            show_message(str(exc), error=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
