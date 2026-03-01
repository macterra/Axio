"""
AxionAgent — Tool Definitions (Native Tool Use)

Generates API tool definitions from the constitution YAML and converts
tool call responses back into CandidateBundle objects for kernel admission.
"""

from __future__ import annotations

from typing import Any, Dict, List

from kernel.src.artifacts import (
    ActionRequest,
    Author,
    CandidateBundle,
    Justification,
    ScopeClaim,
)
from kernel.src.constitution import Constitution


def _build_field_schema(field_def: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a constitution field definition to a JSON Schema property."""
    ftype = field_def.get("type", "string")

    if ftype == "string":
        prop: Dict[str, Any] = {"type": "string"}
        if "max_len" in field_def:
            prop["maxLength"] = field_def["max_len"]
        return prop

    if ftype == "enum":
        return {
            "type": "string",
            "enum": field_def.get("allowed", []),
        }

    if ftype == "int":
        prop = {"type": "integer"}
        if "max_value" in field_def:
            prop["maximum"] = field_def["max_value"]
        return prop

    # Fallback: treat as string
    return {"type": "string"}


def build_tool_definitions(constitution: Constitution) -> List[Dict[str, Any]]:
    """Generate provider-agnostic tool specs from constitution action types.

    Each non-kernel_only action type becomes a tool with:
    - Its constitutional required_fields mapped to JSON Schema properties
    - A required 'justification' string parameter (Option B: authority articulation)

    Returns a list of dicts with keys: name, description, parameters (JSON Schema).
    """
    tools: List[Dict[str, Any]] = []

    for at_def in constitution.data.get("action_space", {}).get("action_types", []):
        if at_def.get("kernel_only"):
            continue

        properties: Dict[str, Any] = {}
        required: List[str] = []

        for field_def in at_def.get("required_fields", []):
            fname = field_def["name"]
            properties[fname] = _build_field_schema(field_def)
            # Fields with defaults are not required in the schema
            if "default" not in field_def:
                required.append(fname)

        # Add justification parameter
        properties["justification"] = {
            "type": "string",
            "description": (
                "Why you have authority to perform this action. "
                "Briefly explain the reasoning that connects the user's request "
                "to this specific action."
            ),
        }
        required.append("justification")

        tools.append({
            "name": at_def["type"],
            "description": at_def.get("description", ""),
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        })

    return tools


def to_anthropic_tools(constitution: Constitution) -> List[Dict[str, Any]]:
    """Convert to Anthropic tool format (input_schema key)."""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["parameters"],
        }
        for t in build_tool_definitions(constitution)
    ]


def to_openai_tools(constitution: Constitution) -> List[Dict[str, Any]]:
    """Convert to OpenAI tool format ({type: 'function', function: {...}})."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in build_tool_definitions(constitution)
    ]


# ---------------------------------------------------------------------------
# Tool call -> CandidateBundle conversion
# ---------------------------------------------------------------------------


def build_candidate_from_tool_call(
    tool_call_name: str,
    tool_call_arguments: Dict[str, Any],
    constitution_version: str,
) -> CandidateBundle:
    """Construct a CandidateBundle from a native tool call.

    The host auto-populates:
    - authority_citations: standard invariant citations
    - scope_claim: clause_ref, observation_ids (placeholder), claim from justification
    - justification: from the justification tool parameter

    The kernel admission pipeline runs identically on the result.
    """
    args = dict(tool_call_arguments)
    justification_text = args.pop("justification", "")

    # Remaining args are the action fields
    ar = ActionRequest(
        action_type=tool_call_name,
        fields=args,
        author=Author.REFLECTION.value,
    )

    sc = ScopeClaim(
        observation_ids=["placeholder"],
        claim=justification_text,
        clause_ref=f"constitution:v{constitution_version}#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
        author=Author.REFLECTION.value,
    )

    just = Justification(
        text=justification_text,
        author=Author.REFLECTION.value,
    )

    return CandidateBundle(
        action_request=ar,
        scope_claim=sc,
        justification=just,
        authority_citations=[
            f"constitution:v{constitution_version}#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            f"constitution:v{constitution_version}#INV-AUTHORITY-CITED",
        ],
    )
