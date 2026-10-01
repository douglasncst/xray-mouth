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
    "OtherPatientIDs",
    "OtherPatientNames",
    "MedicalRecordLocator",
    "EthnicGroup",
    "Occupation",
    "AdditionalPatientHistory",
    "StudyID",
    "RequestingPhysician",
    "PatientComments",
)

UID_KEYWORDS = ("SOPInstanceUID", "StudyInstanceUID", "SeriesInstanceUID")


def anonymize_dataset(dataset: Dataset) -> Dataset:
    """Remove common direct identifiers from a DICOM dataset in memory."""

    result = copy.deepcopy(dataset)
    for keyword in DIRECT_IDENTIFIERS:
        if keyword in result:
            result.data_element(keyword).value = ""
    result.PatientIdentityRemoved = "YES"
    # Do not claim conformance with the much broader DICOM PS3.15 profile.
    result.DeidentificationMethod = "xray-mouth limited direct-identifier removal v0.2"
    result.remove_private_tags()
    for keyword in UID_KEYWORDS:
        if keyword in result:
            result.data_element(keyword).value = generate_uid()
    return result


def anonymize_file(source: Path, destination: Path) -> Path:
    """Write a de-identified copy; never overwrite the source file."""

    if source.resolve() == destination.resolve():
        raise ValueError("destination must differ from source")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("destination already exists")
    dataset = pydicom.dcmread(source)
    anonymized = anonymize_dataset(dataset)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    if temporary.exists() or temporary.is_symlink():
        raise FileExistsError("temporary destination already exists")
    try:
        anonymized.save_as(temporary)
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination
