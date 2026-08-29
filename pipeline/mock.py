import random

# Generates a placeholder value satisfying a JSON Schema (see pipeline/schemas.py),
# so MOCK_MODE can stand in for any schema-constrained run_skill() call without a
# hand-written fake response per step. Scores are randomized within their declared
# range so different mock runs exercise different verdict bands in pipeline.scoring.


def generate_mock(schema: dict):
    schema_type = schema.get("type")

    if schema_type == "object":
        return {
            key: generate_mock(value_schema)
            for key, value_schema in schema.get("properties", {}).items()
        }

    if schema_type == "array":
        item_schema = schema.get("items", {"type": "string"})
        return [generate_mock(item_schema) for _ in range(2)]

    if schema_type == "integer":
        lo = schema.get("minimum", 0)
        hi = schema.get("maximum", 100)
        return random.randint(lo, hi)

    if schema_type == "number":
        lo = schema.get("minimum", 0)
        hi = schema.get("maximum", 100)
        return round(random.uniform(lo, hi), 2)

    if schema_type == "boolean":
        return random.choice([True, False])

    if schema_type == "string":
        if "enum" in schema:
            return random.choice(schema["enum"])
        return "[MOCK_MODE] placeholder text -- no API call was made."

    return None
