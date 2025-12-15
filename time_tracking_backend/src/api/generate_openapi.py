import json
import os

from src.api.main import app


def main():
    """Generate OpenAPI schema and write to interfaces/openapi.json."""
    openapi_schema = app.openapi()
    output_dir = "interfaces"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "openapi.json")
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
