"""Conservative DICOM de-identification helpers."""

from __future__ import annotations

import copy
from pathlib import Path

import pydicom
from pydicom.dataset import Dataset
from pydicom.uid import generate_uid

DIRECT_IDENTIFIERS = (
    "PatientName",
    "PatientID",
    "PatientBirthDate",
    "PatientSex",
    "PatientAddress",
    "PatientTelephoneNumbers",
    "InstitutionName",
    "InstitutionAddress",
    "ReferringPhysicianName",
    "PerformingPhysicianName",
    "OperatorsName",
    "AccessionNumber",
)


def anonymize_dataset(dataset: Dataset) -> Dataset:
    """Remove common direct identifiers from a DICOM dataset in memory."""

    result = copy.deepcopy(dataset)
    for keyword in DIRECT_IDENTIFIERS:
        if keyword in result:
            result.data_element(keyword).value = ""
    result.PatientIdentityRemoved = "YES"
    result.DeidentificationMethod = "xray-mouth basic profile v0.1"
    result.remove_private_tags()
    for keyword in ("SOPInstanceUID", "StudyInstanceUID", "SeriesInstanceUID"):
        if keyword in result:
            result.data_element(keyword).value = generate_uid()
    return result


def anonymize_file(source: Path, destination: Path) -> Path:
    """Write a de-identified copy; never overwrite the source file."""

    if source.resolve() == destination.resolve():
        raise ValueError("destination must differ from source")
    dataset = pydicom.dcmread(source)
    anonymized = anonymize_dataset(dataset)
    destination.parent.mkdir(parents=True, exist_ok=True)
    anonymized.save_as(destination)
    return destination
