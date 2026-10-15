from pathlib import Path

import pytest

from bilingual_glossary.core.store import Glossary

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def glossary(tmp_path):
    library = Glossary(tmp_path / "data")
    library.import_file(ROOT / "examples/terms.json")
    return library
