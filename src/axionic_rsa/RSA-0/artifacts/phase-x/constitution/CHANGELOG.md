# Constitution Changelog

## v0.1.1 (2026-02-10)
- `LogAppend`: replaced `jsonl_line: string` with `jsonl_lines: array<string>`
- `LogAppend`: added per-warrant limits (`max_lines_per_warrant=50`, `max_chars_per_line=10000`, `max_bytes_per_warrant=256000`)
- `RefusalRecord`: removed `INTEGRITY_RISK` from refusal reason codes (integrity risk always triggers EXIT)
- Added `refusal_reason_codes` and `admission_rejection_codes` as explicit closed enums
- Added `rejection_summary_by_gate` to `refusal_output_requirements`
- Added `observation_schema` section with closed `kind` enum and per-kind payload schemas
- Added `trace_event_types` to `telemetry_policy`

## v0.1 (2026-02-10)
- Initial constitution for Phase X (RSA-0)
