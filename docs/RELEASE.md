# Version 0.1.1

Offline Chinese-English terminology search, consistency checks, reviewable repairs and MCP tools.

Local verification: 28 tests passed; 91% measured coverage; Ruff lint and formatting checks passed. README quick start was exercised with fictional data.

## Known limitations

Checks are lexical and scan quoted/code text; they do not resolve meaning or inflection. Ambiguous equal-length aliases resolve deterministically. TBX uses a documented custom extension for lossless self-roundtrip; full external dialect compatibility is not claimed. Aligned PO supports singular entries; XLIFF line positions may be approximate. Fuzzy lookup is intended for modest local libraries.

See README and AGENTS.md for installation, configuration, machine-readable CLI/MCP interfaces and operational boundaries.

This patch corrects the project attribution in the MIT license.
