"""Schema loading and validation utilities."""

import json
from pathlib import Path
from typing import Any, Optional

from jsonschema import Draft202012Validator, RefResolver, ValidationError as JsonSchemaValidationError

from .errors import SchemaValidationError


# Cache for loaded schemas
_schema_cache: dict[str, dict] = {}
_validator_cache: dict[str, Draft202012Validator] = {}


def get_schemas_dir() -> Path:
    """Get the path to the schemas directory."""
    return Path(__file__).parent.parent / "schemas"


def load_schema(schema_name: str) -> dict:
    """Load a JSON schema by name.

    Args:
        schema_name: Schema filename (with or without .json extension)

    Returns:
        Parsed JSON schema dict

    Raises:
        FileNotFoundError: If schema file doesn't exist
    """
    # Add .json extension if not present
    if not schema_name.endswith(".json"):
        schema_name = schema_name + ".json"

    if schema_name in _schema_cache:
        return _schema_cache[schema_name]

    schema_path = get_schemas_dir() / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    _schema_cache[schema_name] = schema
    return schema


def _create_resolver() -> RefResolver:
    """Create a JSON schema ref resolver for local schemas."""
    schemas_dir = get_schemas_dir()

    # Load all schemas for the store
    store = {}
    for schema_file in schemas_dir.glob("*.json"):
        schema = load_schema(schema_file.name)
        schema_id = schema.get("$id", f"file://{schema_file}")
        store[schema_id] = schema
        # Also add by filename for local refs
        store[schema_file.name] = schema

    # Use the common schema as the base
    base_schema = load_schema("common.json")
    base_uri = base_schema.get("$id", "https://axio.local/schema/common.json")

    return RefResolver(base_uri, base_schema, store=store)


def get_validator(schema_name: str) -> Draft202012Validator:
    """Get a cached validator for a schema.

    Args:
        schema_name: Schema filename (e.g., "proposal.json")

    Returns:
        Configured validator instance
    """
    if schema_name in _validator_cache:
        return _validator_cache[schema_name]

    schema = load_schema(schema_name)
    resolver = _create_resolver()

    validator = Draft202012Validator(schema, resolver=resolver)
    _validator_cache[schema_name] = validator
    return validator


def validate_json(data: Any, schema_name: str) -> None:
    """Validate data against a JSON schema.

    Args:
        data: Data to validate
        schema_name: Schema filename (e.g., "proposal.json")

    Raises:
        SchemaValidationError: If validation fails
    """
    validator = get_validator(schema_name)

    errors = list(validator.iter_errors(data))
    if errors:
        # Format error messages
        error_messages = []
        for error in errors[:10]:  # Limit to first 10 errors
            path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "(root)"
            error_messages.append(f"  - {path}: {error.message}")

        raise SchemaValidationError(
            f"Schema validation failed for {schema_name}:\n" + "\n".join(error_messages),
            schema_name=schema_name,
            errors=errors
        )


def validate_proposal(proposal: dict) -> None:
    """Validate a proposal against the proposal schema."""
    validate_json(proposal, "proposal.json")


def validate_trace(trace: dict) -> None:
    """Validate a trace against the trace schema."""
    validate_json(trace, "trace.json")


def validate_env_state(env_state: dict) -> None:
    """Validate environment state against the toy_env schema."""
    validate_json(env_state, "toy_env.json")


def validate_audit_entry(entry: dict) -> None:
    """Validate an audit entry against the audit_entry schema."""
    validate_json(entry, "audit_entry.json")


def validate_capability_token(token: dict) -> None:
    """Validate a capability token against the capability_token schema."""
    validate_json(token, "capability_token.json")


def clear_caches() -> None:
    """Clear all schema and validator caches."""
    _schema_cache.clear()
    _validator_cache.clear()


# Alias for backwards compatibility
validate_with_schema = validate_json
