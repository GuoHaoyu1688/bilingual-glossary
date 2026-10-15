import sqlite3
import zipfile
from collections import Counter
from pathlib import Path

import pytest
from defusedxml.common import DefusedXmlException

from bilingual_glossary.core.checker import Checker, aligned, occurrences
from bilingual_glossary.core.store import Glossary, GlossError, read_terms

ROOT = Path(__file__).resolve().parents[1]


def test_examples_counts_and_idempotency(glossary):
    assert Counter(r["domain"] for r in glossary.list()) == {
        "water-treatment": 30,
        "power-chemistry": 30,
        "it": 30,
    }
    assert glossary.import_file(ROOT / "examples/terms.json") == {
        "inserted": 0,
        "updated": 0,
        "skipped": 90,
        "backup": None,
    }


@pytest.mark.parametrize(
    "query,expected",
    [
        ("fst", "reverse osmosis"),
        ("RO", "reverse osmosis"),
        ("revers osmosis", "reverse osmosis"),
        ("反渗透", "reverse osmosis"),
        ("cyq", "deaerator"),
    ],
)
def test_lookup(glossary, query, expected):
    assert glossary.search(query)[0]["en"] == expected


def test_eight_seeded_findings_without_extras(glossary):
    checker = Checker(glossary)
    issues = checker.check_file(ROOT / "examples/review.md")
    assert Counter(i["code"] for i in issues) == {"INCONSISTENT_VARIANT": 5, "FORBIDDEN_VARIANT": 3}
    assert [i["line"] for i in issues] == list(range(3, 11))
    assert checker.check_file(ROOT / "examples/clean.md") == []


def test_longest_cjk_match_and_latin_boundaries(glossary):
    glossary.add(
        {
            "zh": "锅炉给水",
            "en": "boiler feedwater",
            "domain": "power-chemistry",
            "status": "approved",
        }
    )
    matches = occurrences("锅炉给水", glossary.list())
    assert len(matches) == 1 and matches[0]["term"]["en"] == "boiler feedwater"
    assert not occurrences(
        "action reaction", [r for r in glossary.list() if r["en"] == "ion exchange"]
    )
    assert Checker(glossary).check_pair("锅炉给水", "boiler feedwater") == []


def test_pair_canonical_and_prompt_selection(glossary):
    checker = Checker(glossary)
    assert checker.check_pair("反渗透", "RO") == []
    assert checker.check_pair("反渗透", "reverse osmosis") == []
    issues = checker.check_pair("反渗透", "membrane")
    assert len(issues) == 1 and issues[0]["suggestion"] == "reverse osmosis"
    selection = checker.prompt("反渗透 uses RO.")
    assert len(selection["terms"]) == 1 and "reverse osmosis" in selection["prompt"]
    assert "hardness" not in selection["prompt"]


@pytest.mark.parametrize("format", ["json", "csv", "tbx"])
def test_lossless_roundtrip(glossary, tmp_path, format):
    out = tmp_path / f"export.{format}"
    glossary.export(out, format)
    if format == "csv":
        assert out.read_bytes().startswith(b"\xef\xbb\xbf")
    restored = Glossary(tmp_path / f"restored-{format}")
    restored.import_file(out)
    assert restored.list() == glossary.list()


def test_kb_csv_has_exact_compatible_columns(glossary):
    import csv
    import io

    rows = list(csv.DictReader(io.StringIO(glossary.export_text("csv", kb=True).lstrip("\ufeff"))))
    assert set(rows[0]) == {"zh", "en", "abbr", "definition_zh", "definition_en"}
    assert len(rows) == 90


def test_atomic_import_conflicts_and_backup(glossary, tmp_path):
    before = glossary.list()
    updated = glossary.get("water-treatment-01")
    updated["notes"] = "Reviewed"
    fresh = {"zh": "示例概念", "en": "example concept", "domain": "general"}
    with pytest.raises(GlossError, match="requires"):
        glossary.import_records([fresh, updated])
    assert glossary.list() == before
    result = glossary.import_records([updated], replace=True, confirm=True)
    assert result["updated"] == 1 and result["backup"]
    with zipfile.ZipFile(result["backup"]) as archive:
        archive.extract("glossary.db", tmp_path / "restore")
    with sqlite3.connect(tmp_path / "restore/glossary.db") as con:
        assert con.execute("SELECT notes FROM terms WHERE id='water-treatment-01'").fetchone()[
            0
        ] == next(row["notes"] for row in before if row["id"] == "water-treatment-01")
        assert con.execute("SELECT count(*) FROM terms").fetchone()[0] == 90


def test_update_conflict_and_approval(glossary):
    row = glossary.get("water-treatment-01")
    new = glossary.update(row["id"], {"status": "draft"}, row["updated_at"])
    with pytest.raises(GlossError, match="changed"):
        glossary.update(row["id"], {"notes": "stale"}, row["updated_at"])
    assert Checker(glossary).check_text("hardness and water hardness") == []
    assert new["status"] == "draft"


def test_fix_is_diff_only_until_write_and_has_backup(glossary, tmp_path):
    path = tmp_path / "document.md"
    path.write_text("Use inverse osmosis.\nDo not use electric conductibility.\n")
    checker = Checker(glossary)
    before = path.read_text()
    preview = checker.fix([str(path)])
    assert (
        path.read_text() == before
        and preview["files_changed"] == 1
        and "+Use reverse osmosis." in preview["diffs"][0]["diff"]
    )
    applied = checker.fix([str(path)], write=True)
    assert "inverse osmosis" not in path.read_text() and "conductivity" in path.read_text()
    with zipfile.ZipFile(applied["backup"]) as archive:
        assert archive.read("000_document.md").decode() == before
    assert checker.fix([str(path)], write=True)["files_changed"] == 0


def test_delete_confirmation_backup_and_not_found(glossary):
    with pytest.raises(GlossError, match="requires"):
        glossary.delete("water-treatment-01")
    result = glossary.delete("water-treatment-01", True)
    assert result["backup"]
    with pytest.raises(GlossError) as info:
        glossary.get("water-treatment-01")
    assert info.value.exit_code == 3


@pytest.mark.parametrize(
    "suffix,text",
    [
        (".md", "反渗透\n\nreverse osmosis\n\n除氧器\n\nunrelated equipment\n"),
        (".csv", "zh,en\n反渗透,reverse osmosis\n除氧器,unrelated equipment\n"),
        (
            ".po",
            'msgid "反渗透"\nmsgstr "reverse osmosis"\n\nmsgid "除氧器"\nmsgstr "unrelated equipment"\n',
        ),
        (
            ".xlf",
            '<xliff><file><body><trans-unit id="a"><source>反渗透</source><target>reverse osmosis</target></trans-unit><trans-unit id="b"><source>除氧器</source><target>unrelated equipment</target></trans-unit></body></file></xliff>',
        ),
    ],
)
def test_alignment_formats(glossary, tmp_path, suffix, text):
    path = tmp_path / ("pair" + suffix)
    path.write_text(text)
    issues = Checker(glossary).check_file(path, pair="zh,en")
    assert len(issues) == 1 and issues[0]["suggestion"] == "deaerator"


def test_unsafe_xml_and_bad_alignment_rejected():
    with pytest.raises(DefusedXmlException):
        read_terms('<!DOCTYPE tbx [<!ENTITY x SYSTEM "file:///etc/passwd">]><tbx>&x;</tbx>', "tbx")
    with pytest.raises(GlossError):
        aligned("one unpaired paragraph", ".md", "zh", "en")
    with pytest.raises(GlossError):
        read_terms("<unknown/>", "tbx")


def test_invalid_fields_and_duplicates_rollback(glossary):
    for record in [
        {"zh": "示例", "en": ""},
        {"zh": "示例", "en": "sample", "status": "bad"},
        {"zh": "示例", "en": "sample", "synonyms_en": [""]},
        {"zh": "示例", "en": "sample", "forbidden": ["sample"]},
    ]:
        with pytest.raises(GlossError):
            glossary.add(record)
    rows = [{"zh": "重复", "en": "duplicate", "domain": "general"}] * 2
    with pytest.raises(GlossError):
        glossary.import_records(rows)
    assert len(glossary.list()) == 90


def test_external_tbx_subset_preserves_variant_status(tmp_path):
    text = """<tbx xmlns="urn:iso:std:iso:30042:ed-2"><text><body><conceptEntry id="sample">
    <descrip type="subjectField">general</descrip>
    <langSec xml:lang="zh"><termSec><term>示例</term></termSec><descrip type="definition">Sample definition</descrip></langSec>
    <langSec xml:lang="en"><termSec><term>sample</term><termNote type="administrativeStatus">preferredTerm</termNote></termSec><termSec><term>example</term><termNote type="administrativeStatus">admittedTerm</termNote></termSec><termSec><term>bad sample</term><termNote type="administrativeStatus">deprecatedTerm</termNote></termSec></langSec>
    </conceptEntry></body></text></tbx>"""
    library = Glossary(tmp_path / "external")
    library.import_records(read_terms(text, "tbx"))
    row = library.get("sample")
    assert row["en"] == "sample" and row["synonyms_en"] == ["example"]
    assert row["forbidden"] == [{"lang": "en", "text": "bad sample"}]
    assert row["definition_zh"] == "Sample definition"
