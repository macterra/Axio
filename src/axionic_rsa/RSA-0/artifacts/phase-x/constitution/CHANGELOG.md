# Constitution Changelog

## v0.2 (2026-02-12)
- Added 4 ECK sections: AmendmentProcedure, AuthorityModel, WarrantDefinition, ScopeSystem
- Enabled constitutional self-amendment (`amendments_enabled: true`)
- Added 5 authority identifiers: AUTH_TELEMETRY, AUTH_IO_READ, AUTH_IO_WRITE, AUTH_GOVERNANCE, AUTH_EXECUTION
- Added explicit `action_permissions` and `amendment_permissions` mappings
- Set `authority_reference_mode: BOTH` with explicit `CL-AUTHORITY-REFERENCE-MODE` definition
- Added 20 CL-* clause IDs for all new law clauses (INV-* remains valid and citable)
- Removed Exit from `action_types` (Exit remains a policy decision type)
- Added `constitutions` and `amendment_trace` log streams
- Added 10 new admission rejection codes for amendment gates (18 total)
- Added `max_constitution_bytes: 32768`
- Added amendment budget caps (`max_amendment_candidates_per_cycle`, `max_pending_amendments`)
- Added `AmendmentProposal` and `AmendmentAdoptionRecord` to `artifact_vocabulary`
- Added `propose_amendments` to `reflection_policy.llm_role`
- Replaced `amend` with `adopt_amendment` in `reflection_policy.llm_forbidden`
- Enforced schema closure (`additionalProperties: false`)
- Added `CL-DENSITY-DEFINITION`: A counted from action_permissions authorities only
- Added `CL-CITATION-FORMATS`: explicit citation namespace definitions
- Added `CL-KERNEL-CITATION-RULE`: kernel-only actions must self-cite AUTH_TELEMETRY
- Added `CL-AMENDMENT-ARTIFACT-RULES`: required fields + to_dict_id serialization
- Added `CL-AMENDMENT-FAILURE-ROUTING`: amendment gate failures → admission rejections, not RefusalRecords
- Clarified ScopeClaim not applicable to AmendmentProposals (`amendment_proposal_scope_rule`)
- Fixed ScopeSystem statement to note LogAppend exemption
- Density: A=3, B=4, M=4, density=0.3333 (bound=0.75)

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
