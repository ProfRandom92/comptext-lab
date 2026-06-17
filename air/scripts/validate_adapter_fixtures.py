import json
import sys
from pathlib import Path
from collections import OrderedDict

ADAPTER_FIXTURES_DIR = Path("fixtures/adapter")
INVALID_FIXTURES_DIR = ADAPTER_FIXTURES_DIR / "invalid"
REPORT_OUTPUT = Path("reports/generated/adapter-validation-report.json")

VALID_KIND = {"local-cli", "mcp-proxy", "internal-vfs", "unknown"}
VALID_AIR_VERSION = "air-v0.1"

REQUIRED_TOP = [
    "adapter_id",
    "adapter_kind",
    "supported_air_version",
    "command_surface",
    "input_mapping",
    "output_mapping",
    "evidence_mapping",
    "disabled_capabilities"
]

FORBIDDEN_CLAIMS = {
    "provider_runtime",
    "mcp_server",
    "external_agent_execution",
    "auto_apply",
    "network_required",
    "production_runtime",
    "legal_assurance",
    "compliance_assurance",
    "forensic_assurance"
}

def validate_adapter(fixture, fixture_path):
    if not isinstance(fixture, dict):
        raise ValueError(f"{fixture_path}: Adapter must be an object")

    for key in REQUIRED_TOP:
        if key not in fixture:
            raise ValueError(f"{fixture_path}: missing required field: {key}")

    if fixture["adapter_kind"] not in VALID_KIND:
        raise ValueError(f"{fixture_path}: invalid adapter_kind: {fixture['adapter_kind']}")

    if fixture["supported_air_version"] != VALID_AIR_VERSION:
        raise ValueError(f"{fixture_path}: unsupported air version: {fixture['supported_air_version']}")

    # Check for forbidden claims
    for claim in FORBIDDEN_CLAIMS:
        if claim in fixture:
            raise ValueError(f"{fixture_path}: forbidden claim found: {claim}")

    # Validate command_surface
    cs = fixture["command_surface"]
    if not isinstance(cs, dict) or "binary" not in cs or "commands" not in cs:
        raise ValueError(f"{fixture_path}: invalid command_surface structure")
    
    if not isinstance(cs["commands"], list):
        raise ValueError(f"{fixture_path}: command_surface.commands must be a list")

    # Validate input_mapping
    im = fixture["input_mapping"]
    if not isinstance(im, list):
        raise ValueError(f"{fixture_path}: input_mapping must be a list")
    for mapping in im:
        if not all(k in mapping for k in ["air_input_kind", "runtime_flag"]):
            raise ValueError(f"{fixture_path}: invalid input_mapping entry")

    # Validate output_mapping
    om = fixture["output_mapping"]
    if not isinstance(om, list):
        raise ValueError(f"{fixture_path}: output_mapping must be a list")
    for mapping in om:
        if not all(k in mapping for k in ["runtime_key", "air_output_kind"]):
            raise ValueError(f"{fixture_path}: invalid output_mapping entry")

def validate_adapter_fixtures():
    print("Validating AIR Adapter fixtures...")
    
    report = OrderedDict([
        ("status", "failure"),
        ("checked_files", []),
        ("invalid_fixtures_failures", []),
        ("forbidden_claims_blocked", sorted(list(FORBIDDEN_CLAIMS)))
    ])

    error_count = 0

    # 1. Validate positive fixtures
    positive_fixtures = list(ADAPTER_FIXTURES_DIR.glob("*.json"))
    for fixture_path in positive_fixtures:
        print(f"  Validating {fixture_path}...")
        report["checked_files"].append(str(fixture_path))
        try:
            with open(fixture_path, 'r') as f:
                fixture = json.load(f)
            validate_adapter(fixture, fixture_path)
        except Exception as e:
            print(f"FAILURE: {fixture_path} should be valid but failed: {e}")
            error_count += 1

    # 2. Validate negative fixtures
    if INVALID_FIXTURES_DIR.exists():
        negative_fixtures = list(INVALID_FIXTURES_DIR.glob("*.json"))
        for fixture_path in negative_fixtures:
            print(f"  Validating {fixture_path} (expecting failure)...")
            report["checked_files"].append(str(fixture_path))
            try:
                with open(fixture_path, 'r') as f:
                    fixture = json.load(f)
                validate_adapter(fixture, fixture_path)
                print(f"FAILURE: {fixture_path} should be invalid but passed")
                error_count += 1
            except Exception as e:
                print(f"  {fixture_path} failed as expected: {e}")
                report["invalid_fixtures_failures"].append({
                    "file": str(fixture_path),
                    "error": str(e)
                })

    if error_count == 0:
        report["status"] = "success"

    # Write report
    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"  Report generated: {REPORT_OUTPUT}")

    if error_count > 0:
        print(f"\nValidation failed with {error_count} errors.")
        sys.exit(1)

    print("\nSUCCESS: All adapter fixtures validated correctly (including negative tests).")

if __name__ == "__main__":
    validate_adapter_fixtures()
