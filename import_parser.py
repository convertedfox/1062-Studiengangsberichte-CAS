from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from zipfile import ZipFile
import xml.etree.ElementTree as ET

DATA_DIR = Path("data")

COL_STUDIENGANG = "A"
COL_FACHBEREICH = "B"
STUDIENANFANGER_COLS = {"-4": "C", "-3": "D", "-2": "E", "-1": "F"}
IMMATRIKULIERTE_COLS = {"-4": "G", "-3": "H", "-2": "I", "-1": "J"}
COL_VORSTUDIUM_PROFIL = "K"
COL_ERFOLGSQUOTE = "L"
COL_FACHSEMESTER = "M"
COL_BERUFSERFAHRUNG = "N"
COL_ALTER = "O"
COL_DOZENTEN_HERKUNFT = "P"
COL_MODULE_BELEGUNG = "Q"
COL_MODULTEILNEHMER = "R"
COL_MODULAUSLASTUNG = "S"
COL_ANZAHL_MODULE = "T"


@dataclass(frozen=True)
class StudyProgramRow:
    studiengang: str
    fachbereich: str
    studienanfaenger: dict[str, Optional[int]]
    immatrikulierte: dict[str, Optional[int]]
    vorstudium_profil: dict[str, Optional[float]]
    erfolgsquote: Optional[float]
    fachsemester: Optional[float]
    berufserfahrung: Optional[float]
    alter: Optional[float]
    dozenten_herkunft_profil: dict[str, Optional[float]]
    module_belegung_nach_sg: dict[str, Optional[float]]
    modulteilnehmer_herkunft: dict[str, Optional[float]]
    modulauslastung: Optional[float]
    anzahl_module: Optional[int]


def load_latest_import_table(data_dir: Path = DATA_DIR) -> list[StudyProgramRow]:
    import_path = _find_latest_import(data_dir)
    raw_rows = _read_sheet_rows(import_path, sheet_name="Importtabelle")
    return _parse_import_rows(raw_rows)


def _find_latest_import(data_dir: Path) -> Path:
    candidates = sorted(data_dir.glob("Import *.xlsx"))
    if not candidates:
        raise FileNotFoundError(f"No Import *.xlsx files found in {data_dir}")
    return max(candidates)


def _read_sheet_rows(import_path: Path, sheet_name: str) -> list[dict[str, str]]:
    with ZipFile(import_path) as zf:
        sheet_path = _resolve_sheet_path(zf, sheet_name)
        shared_strings = _read_shared_strings(zf)
        sheet_xml = ET.fromstring(zf.read(sheet_path))
        rows: list[dict[str, str]] = []
        for row in sheet_xml.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
            row_data: dict[str, str] = {}
            for cell in row.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
                cell_ref = cell.attrib.get("r")
                if not cell_ref:
                    continue
                col = "".join(ch for ch in cell_ref if ch.isalpha())
                value_node = cell.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
                value = value_node.text if value_node is not None else ""
                if cell.attrib.get("t") == "s":
                    value = shared_strings.get(int(value), "")
                row_data[col] = value
            rows.append(row_data)
        return rows


def _resolve_sheet_path(zf: ZipFile, sheet_name: str) -> str:
    wb_xml = ET.fromstring(zf.read("xl/workbook.xml"))
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    sheet_id = None
    for sheet in wb_xml.findall("main:sheets/main:sheet", ns):
        if sheet.attrib.get("name") == sheet_name:
            sheet_id = sheet.attrib.get(
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            )
            break
    if not sheet_id:
        raise KeyError(f"Sheet '{sheet_name}' not found in workbook.")

    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    target = None
    for rel in rels.findall("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
        if rel.attrib.get("Id") == sheet_id:
            target = rel.attrib.get("Target")
            break
    if not target:
        raise KeyError(f"Could not resolve sheet path for '{sheet_name}'.")
    return f"xl/{target}"


def _read_shared_strings(zf: ZipFile) -> dict[int, str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return {}
    sst_xml = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings: dict[int, str] = {}
    for idx, si in enumerate(
        sst_xml.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si")
    ):
        texts = [
            t.text or ""
            for t in si.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
        ]
        strings[idx] = "".join(texts)
    return strings


def _parse_import_rows(rows: list[dict[str, str]]) -> list[StudyProgramRow]:
    parsed: list[StudyProgramRow] = []
    for row in rows[1:]:
        studiengang = _normalize_text(row.get(COL_STUDIENGANG, ""))
        if not studiengang:
            continue
        fachbereich = _normalize_text(row.get(COL_FACHBEREICH, ""))
        studienanfaenger = {
            key: _parse_optional_int(row.get(col, "")) for key, col in STUDIENANFANGER_COLS.items()
        }
        immatrikulierte = {
            key: _parse_optional_int(row.get(col, "")) for key, col in IMMATRIKULIERTE_COLS.items()
        }
        parsed.append(
            StudyProgramRow(
                studiengang=studiengang,
                fachbereich=fachbereich,
                studienanfaenger=studienanfaenger,
                immatrikulierte=immatrikulierte,
                vorstudium_profil=_parse_profile(row.get(COL_VORSTUDIUM_PROFIL, "")),
                erfolgsquote=_parse_optional_float(row.get(COL_ERFOLGSQUOTE, "")),
                fachsemester=_parse_optional_float(row.get(COL_FACHSEMESTER, "")),
                berufserfahrung=_parse_optional_float(row.get(COL_BERUFSERFAHRUNG, "")),
                alter=_parse_optional_float(row.get(COL_ALTER, "")),
                dozenten_herkunft_profil=_parse_profile(row.get(COL_DOZENTEN_HERKUNFT, "")),
                module_belegung_nach_sg=_parse_profile(row.get(COL_MODULE_BELEGUNG, "")),
                modulteilnehmer_herkunft=_parse_profile(row.get(COL_MODULTEILNEHMER, "")),
                modulauslastung=_parse_optional_float(row.get(COL_MODULAUSLASTUNG, "")),
                anzahl_module=_parse_optional_int(row.get(COL_ANZAHL_MODULE, "")),
            )
        )
    return parsed


def _parse_profile(value: str) -> dict[str, Optional[float]]:
    raw = _normalize_text(value)
    if not raw:
        return {}
    if raw.startswith("{") and raw.endswith("}"):
        raw = raw[1:-1].strip()
    if not raw:
        return {}
    entries = [part.strip() for part in raw.split(";") if part.strip()]
    profile: dict[str, Optional[float]] = {}
    for entry in entries:
        if ":" not in entry:
            raise ValueError(f"Invalid profile entry: {entry}")
        key, raw_value = entry.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        profile[key] = _parse_optional_float(raw_value)
    return profile


def _parse_optional_int(value: str) -> Optional[int]:
    raw = _normalize_text(value)
    if raw == "":
        return None
    number = _parse_float(raw)
    if not number.is_integer():
        raise ValueError(f"Expected integer, got {value}")
    return int(number)


def _parse_optional_float(value: str) -> Optional[float]:
    raw = _normalize_text(value)
    if raw == "":
        return None
    return _parse_float(raw)


def _parse_float(value: str) -> float:
    normalized = value.replace(",", ".")
    return float(normalized)


def _normalize_text(value: str) -> str:
    return str(value).strip()
