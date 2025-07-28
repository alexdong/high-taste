from pathlib import Path

import yaml


def literal_presenter(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    """
    Represent every string that contains at least one newline with the
    block-literal style (|).  All other strings fall back to the default.
    """
    if "\n" in data:                      # multi-line => use '|'
        # style='|' ⇒ literal, style='>' ⇒ folded
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)

# Register for the dumper you intend to use
yaml.add_representer(str, literal_presenter, Dumper=yaml.SafeDumper)

def serialise_yaml(data: dict, file_path: Path) -> None:
    """Write the given data to a YAML file."""
    yaml_file_path = file_path.parent / f"{file_path.stem}.yaml"
    yaml_content = yaml.dump(
        data,
        Dumper=yaml.SafeDumper,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    yaml_file_path.write_text(yaml_content, encoding="utf-8")


if __name__ == "__main__":
    import tempfile
    
    # Example usage demonstrating multi-line string handling
    example_data = {
        "rule_name": "Use assertions over exceptions",
        "rule_id": "FAILFAST001",
        "description": "Prefer assert statements for design contract enforcement.\nThey make code intent clearer and fail fast during development.",
        "example": {
            "bad": """def process_data(data):
    if not data:
        raise ValueError("Data cannot be empty")
    # process data...""",
            "good": """def process_data(data):
    assert data, "Data cannot be empty"
    # process data..."""
        },
        "problems": ["readability", "debugging", "fail-fast"],
        "severity": "warning"
    }
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    serialise_yaml(example_data, tmp_path)
    print(f"✅ Written example YAML to {tmp_path}")
    
    # Read and display the output to show multi-line formatting
    print("\n📄 Generated YAML content:")
    print("-" * 50)
    yaml_content = tmp_path.read_text()
    print(yaml_content)
    
    # Clean up temporary file
    tmp_path.unlink()
    print("\n🧹 Cleaned up temporary file")
