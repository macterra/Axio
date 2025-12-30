"""JSON Schema loading and validation for AKI.

Handles:
- Loading schemas from the schemas/ directory
- $ref resolution for local file references
- Validation of objects against schemas
"""

import json
from pathlib import Path
from typing import Any, Optional

import jsonschema
from jsonschema import Draft202012Validator, RefResolver

from .errors import SchemaValidationError


# Cache for loaded schemas
_schema_cache: dict[str, dict] = {}
_validators: dict[str, Draft202012Validator] = {}


def get_schema_dir() -> Path:
    """Get the path to the schemas directory."""
    return Path(__file__).parent.parent / "schemas"


def load_schema(schema_name: str) -> dict:
    """Load a JSON schema by name.

    Args:
        schema_name: Name of the schema file (e.g., "proposal.json")

    Returns:
        Parsed schema dict

    Raises:
        FileNotFoundError: If schema file doesn't exist
    """
    if schema_name in _schema_cache:
        return _schema_cache[schema_name]

    schema_path = get_schema_dir() / schema_name
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    _schema_cache[schema_name] = schema
    return schema


def get_validator(schema_name: str) -> Draft202012Validator:
    """Get a cached validator for a schema.

    Args:
        schema_name: Name of the schema file

    Returns:
        Configured validator with $ref resolution
    """
    if schema_name in _validators:
        return _validators[schema_name]

    schema = load_schema(schema_name)
    schema_dir = get_schema_dir()

    # Create a resolver that can handle local $ref
    resolver = RefResolver(
        base_uri=f"file://{schema_dir}/",
        referrer=schema,
        handlers={"file": _file_handler}
    )

    validator = Draft202012Validator(schema, resolver=resolver)
    _validators[schema_name] = validator
    return validator


def _file_handler(uri: str) -> dict:
    """Handler for file:// URIs in $ref resolution."""
    # Extract path from file:// URI
    if uri.startswith("file://"):
        path = uri[7:]
    else:
        path = uri

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_object(obj: Any, schema_name: str) -> None:
    """Validate an object against a schema.

    Args:
        obj: Object to validate
        schema_name: Name of the schema file

    Raises:
        SchemaValidationError: If validation fails
    """
    validator = get_validator(schema_name)

    errors = list(validator.iter_errors(obj))
    if errors:
        # Format the first error for the message
        first_error = errors[0]
        path = ".".join(str(p) for p in first_error.path) if first_error.path else "<root>"
        raise SchemaValidationError(
            schema_name,
            f"at '{path}': {first_error.message}"
        )


def is_valid(obj: Any, schema_name: str) -> bool:
    """Check if an object is valid against a schema.

    Args:
        obj: Object to validate
        schema_name: Name of the schema file

    Returns:
        True if valid, False otherwise
    """
    try:
        validate_object(obj, schema_name)
        return True
    except SchemaValidationError:
        return False


def clear_cache() -> None:
    """Clear the schema cache. Useful for testing."""
    _schema_cache.clear()
    _validators.clear()
