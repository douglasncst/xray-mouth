from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas as pdf_canvas

from xray_mouth.config import RenderConfig, WorkflowConfig
from xray_mouth.devices.folder import FolderImageSource
from xray_mouth.domain import DEFAULT_PROTOCOL, Exam, ExportResult, Protocol
from xray_mouth.exceptions import InputValidationError
from xray_mouth.imaging import map_radiographs
from xray_mouth.layout import build_series_image
from xray_mouth.reporting import write_report


def timestamped_result_directory(output_root: Path, timestamp: datetime | None = None) -> Path:
    stamp = (timestamp or datetime.now()).strftime("%Y%m%d-%H%M%S")
    candidate = output_root / f"xray-mouth-{stamp}"
    suffix = 1
    while candidate.exists():
        candidate = output_root / f"xray-mouth-{stamp}-{suffix:02d}"
        suffix += 1
    return candidate


def create_demo_images(directory: Path, protocol: Protocol = DEFAULT_PROTOCOL) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for slot in protocol.slots:
        image = Image.new("L", (600, 900), color=20 + slot.number * 8)
        draw = ImageDraw.Draw(image)
        draw.ellipse((120, 80, 480, 820), outline=220, width=12)
        draw.line((300, 170, 300, 730), fill=150, width=7)
        draw.text((30, 30), f"SIMULATED {slot.prefix}", fill=255)
        image.save(directory / f"{slot.prefix}_simulated.png")


def _write_pdf(image_path: Path, pdf_path: Path) -> None:
    page_width, page_height = landscape(A4)
    document = pdf_canvas.Canvas(str(pdf_path), pagesize=(page_width, page_height))
    document.setFillColorRGB(0, 0, 0)
    document.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    document.drawImage(
        str(image_path),
        0,
        0,
        width=page_width,
        height=page_height,
        preserveAspectRatio=True,
        anchor="c",
    )
    document.showPage()
    document.save()


def run_workflow(config: WorkflowConfig, protocol: Protocol = DEFAULT_PROTOCOL) -> ExportResult:
    if not config.patient_name.strip():
        raise InputValidationError("Patient name must not be empty.")
    input_directory = config.input_directory
    if config.demo:
        input_directory.mkdir(parents=True, exist_ok=True)
        create_demo_images(input_directory, protocol)
    source_paths = FolderImageSource(input_directory).image_paths()
    if not source_paths:
        raise InputValidationError(
            "No supported radiograph images were found in the input directory."
        )
    radiographs = map_radiographs(source_paths, protocol)
    if not radiographs:
        raise InputValidationError("No files with valid two-digit protocol prefixes were found.")
    missing = tuple(slot.number for slot in protocol.slots if slot.number not in radiographs)
    if config.strict and missing:
        formatted = ", ".join(f"{number:02d}" for number in missing)
        raise InputValidationError(
            f"Strict mode requires a complete series; missing slots: {formatted}"
        )
    output_directory = timestamped_result_directory(config.output_root)
    output_directory.mkdir(parents=True, exist_ok=False)
    exam = Exam(patient_name=config.patient_name.strip(), demo=config.demo)
    render = RenderConfig(contrast=config.contrast)
    preview_path = output_directory / "periapical_series_preview.png"
    render_path = output_directory / "periapical_series_600dpi.png"
    pdf_path = output_directory / "periapical_series.pdf"
    report_path = output_directory / "report.txt"
    build_series_image(radiographs, exam, protocol, render.preview_size, render.contrast).save(
        preview_path
    )
    build_series_image(radiographs, exam, protocol, render.detail_size, render.contrast).save(
        render_path
    )
    _write_pdf(render_path, pdf_path)
    write_report(report_path, exam, protocol, set(radiographs))
    return ExportResult(
        output_directory,
        preview_path,
        render_path,
        pdf_path,
        report_path,
        tuple(sorted(radiographs)),
        missing,
    )
