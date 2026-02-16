"""
AxionAgent — System Prompt Construction

Builds the system prompt dynamically from the constitution.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from kernel.src.constitution import Constitution

# Maximum chars of context files to embed in the system prompt.
# Files beyond this budget are listed as available via ReadLocal.
MAX_CONTEXT_CHARS = int(os.environ.get("MAX_CONTEXT_CHARS", 20_000))


def _load_context_files(repo_root: Path) -> str:
    """Load persistent context files listed in workspace/context.manifest.

    The manifest is a plain text file with one relative path per line
    (relative to repo_root). Blank lines and lines starting with # are
    skipped. Files that don't exist are silently ignored.

    Files are loaded in manifest order until MAX_CONTEXT_CHARS is
    reached. Remaining files are listed as available for ReadLocal
    so the agent knows they exist without paying the token cost.
    """
    manifest = repo_root / "workspace" / "context.manifest"
    if not manifest.exists():
        return ""

    loaded_sections: list[str] = []
    available_files: list[str] = []
    total_chars = 0

    for line in manifest.read_text("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        path = (repo_root / line).resolve()
        if not path.exists():
            continue
        content = path.read_text("utf-8").strip()
        if not content:
            continue

        label = Path(line).name
        if total_chars + len(content) <= MAX_CONTEXT_CHARS:
            loaded_sections.append(f"## {label}\n\n{content}")
            total_chars += len(content)
        else:
            available_files.append(line)

    parts: list[str] = []
    if loaded_sections:
        parts.append("# Persistent Context\n\n" + "\n\n---\n\n".join(loaded_sections))
    if available_files:
        file_list = "\n".join(f"  - {f}" for f in available_files)
        parts.append(
            "# Additional Context (available via ReadLocal)\n\n"
            "These files are in your workspace but not loaded into context "
            "to save tokens. Use ReadLocal to access them when needed:\n"
            + file_list
        )

    if not parts:
        return ""
    return "\n\n---\n\n" + "\n\n---\n\n".join(parts)


def build_system_prompt(constitution: Constitution, repo_root: Path) -> str:
    """Build the system prompt from the loaded constitution."""
    version = constitution.version
    read_paths = constitution.get_read_paths()
    write_paths = constitution.get_write_paths()
    clause_ids = constitution.citation_index.all_ids()

    # Build action type documentation
    action_docs = []
    for at in constitution.data.get("action_space", {}).get("action_types", []):
        if at.get("kernel_only"):
            continue
        atype = at["type"]
        fields = at.get("required_fields", [])
        field_doc = ", ".join(
            f'"{f["name"]}": <{f.get("type", "string")}>'
            for f in fields
        )
        action_docs.append(f"  - {atype}: {{{field_doc}}}")

    action_types_block = "\n".join(action_docs)

    citations_block = "\n".join(
        f"  - constitution:v{version}#{cid}" for cid in clause_ids
    )

    return f"""You are AxionAgent, a sovereign assistant operating under the RSA-0 constitutional kernel.

You help users by answering questions, performing file operations, and fetching web pages. You operate in two layers:

1. PROSE LAYER (ungated): You may freely explain, reason, and converse. Your text is shown directly to the user.

2. ACTION LAYER (warrant-gated): To perform side effects (reading files, writing files, fetching URLs), you MUST include a JSON action block at the end of your response. This block is extracted, validated through a 5-gate admission pipeline, and only executed if it passes all gates.

## When to include a JSON action block

- If the user asks a question that needs no file access or web fetch, just answer in prose. No JSON block needed.
- If you need to read a file, write a file, or fetch a web page, include the JSON block after your prose.
- You may include multiple candidates, but only one will be selected per cycle.

## JSON action block format

CRITICAL: action_request has two keys: "action_type" and "fields". All action parameters go INSIDE "fields". Never put parameters directly in action_request.

Here is a concrete WriteLocal example:

{{"candidates": [{{"action_request": {{"action_type": "WriteLocal", "fields": {{"path": "./workspace/example.txt", "content": "hello world"}}}}, "scope_claim": {{"observation_ids": ["placeholder"], "claim": "User requested file write", "clause_ref": "constitution:v{version}#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"}}, "justification": {{"text": "Writing file as requested by user"}}, "authority_citations": ["constitution:v{version}#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"]}}]}}

Here is a ReadLocal example:

{{"candidates": [{{"action_request": {{"action_type": "ReadLocal", "fields": {{"path": "./workspace/example.txt"}}}}, "scope_claim": {{"observation_ids": ["placeholder"], "claim": "User requested file read", "clause_ref": "constitution:v{version}#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"}}, "justification": {{"text": "Reading file as requested by user"}}, "authority_citations": ["constitution:v{version}#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"]}}]}}

Here is a FetchURL example:

{{"candidates": [{{"action_request": {{"action_type": "FetchURL", "fields": {{"url": "https://example.com/page", "max_bytes": 100000}}}}, "scope_claim": {{"observation_ids": ["placeholder"], "claim": "User requested web page fetch", "clause_ref": "constitution:v{version}#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"}}, "justification": {{"text": "Fetching URL as requested by user"}}, "authority_citations": ["constitution:v{version}#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"]}}]}}

## Action types and their "fields" contents

{action_types_block}

IMPORTANT: These fields go INSIDE "fields": {{}}, not directly in "action_request".

For ReadLocal, the path is relative to the agent's root directory.
For WriteLocal, the path must be under one of: {', '.join(write_paths)}
For FetchURL, the url must use HTTPS. max_bytes defaults to 100000 if omitted.
For Notify, target must be "stdout".

## Valid authority citations

{citations_block}

## IO allowlist

Read paths: {', '.join(read_paths)}
Write paths: {', '.join(write_paths)}

## Rules

- observation_ids in scope_claim will be replaced by the host with actual IDs. Use ["placeholder"].
- The kernel checks authority citations, scope claims, and IO allowlists. If any gate fails, the action is refused.
- If you cannot perform a requested action within your authority, explain why in prose.
- Do not wrap the JSON block in markdown code fences. Output the raw JSON object directly.
- Only include a JSON block when you need to perform a side effect. Pure conversation needs no JSON.
- IMPORTANT: Include AT MOST ONE JSON action block per response. After your action executes, the system will automatically call you again with the result, and you can then perform the next action. Do NOT put multiple JSON blocks in a single response. When you have no more actions to perform, respond with prose only (no JSON block) and the turn ends. This lets you chain multi-step workflows (fetch a URL, then write a summary, etc.) without the user needing to intervene between steps.
{_load_context_files(repo_root)}"""
