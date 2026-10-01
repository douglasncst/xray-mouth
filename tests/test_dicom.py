from pathlib import Path

import pydicom
import pytest
from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from xray_mouth.dicom import anonymize_dataset, anonymize_file


def make_dataset() -> Dataset:
    dataset = Dataset()
    dataset.PatientName = "Example^Person"
    dataset.PatientID = "12345678"
    dataset.StudyInstanceUID = generate_uid()
    dataset.SeriesInstanceUID = generate_uid()
    dataset.SOPInstanceUID = generate_uid()
    return dataset


def test_anonymize_dataset_removes_direct_identifiers() -> None:
    original = make_dataset()
    original_uid = original.StudyInstanceUID

    result = anonymize_dataset(original)

    assert result.PatientName == ""
    assert result.PatientID == ""
    assert result.PatientIdentityRemoved == "YES"
    assert result.StudyInstanceUID != original_uid
    assert original.PatientName == "Example^Person"


def test_anonymize_file_never_overwrites_source(tmp_path: Path) -> None:
    path = tmp_path / "image.dcm"
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = generate_uid()
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    dataset = FileDataset(path, {}, file_meta=file_meta, preamble=b"\0" * 128)
    dataset.PatientName = "Example^Person"
    dataset.SOPClassUID = file_meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    dataset.save_as(path)

    with pytest.raises(ValueError):
        anonymize_file(path, path)

    destination = tmp_path / "clean.dcm"
    anonymize_file(path, destination)
    assert pydicom.dcmread(destination).PatientName == ""
