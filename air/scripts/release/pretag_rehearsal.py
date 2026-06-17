from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = [
    "README.md",
    "PROJEKT.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/VALIDATION_BASELINE.md",
    "docs/RELEASE_READINESS.md",
    "docs/TAGGING_CHECKLIST.md",
    "docs/RELEASE_NOTES_v0.1.0-pre.md",
    "docs/AUDIT_REPORTS.md",
    "docs/AGENT_SKILLS.md",
]

FORBIDDEN_POSITIVE_CLAIMS = [
    "provider runtime is implemented",
    "provider runtime implemented",
    "mcp server is implemented",
    "production mcp is supported",
    "production mcp support is available",
    "hidden chain-of-thought capture is implemented",
    "legal assurance is provided",
    "compliance assurance is provided",
    "forensic assurance is provided",
]

def run(cmd):
    print("$ " + " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    if result.returncode != 0:
        raise SystemExit(result.returncode)

def main():
    print("CompText AIR v0.1.0-pre rehearsal")
    print("NO TAG WILL BE CREATED")
    print("NO GITHUB RELEASE WILL BE CREATED")
    print()

    for rel in REQUIRED:
        path = ROOT / rel
        if not path.exists():
            raise SystemExit(f"missing required file: {rel}")
        print(f"OK file exists: {rel}")

    combined = "\n".join((ROOT / rel).read_text(encoding="utf-8").lower() for rel in REQUIRED)
    for phrase in FORBIDDEN_POSITIVE_CLAIMS:
        if phrase in combined:
            raise SystemExit(f"forbidden positive overclaim phrase found: {phrase}")
    print("OK no forbidden positive overclaim phrases found")

    project = (ROOT / "PROJEKT.md").read_text(encoding="utf-8")
    required_project = [
        "CURRENT_PHASE: 12",
        "CURRENT_TASK: Final pre-tag audit",
        "STATUS: phase-12-final-pre-tag-audit",
    ]
    for item in required_project:
        if item not in project:
            raise SystemExit(f"missing project metadata: {item}")
        print(f"OK project metadata: {item}")

    release_notes = ROOT / "docs/RELEASE_NOTES_v0.1.0-pre.md"
    notes = release_notes.read_text(encoding="utf-8")
    for item in [
        "v0.1.0-pre",
        "pre-release",
        "provider runtime",
        "MCP",
        "hidden chain-of-thought",
    ]:
        if item not in notes:
            raise SystemExit(f"release notes missing expected wording: {item}")
        print(f"OK release notes mention: {item}")

    print()
    print("Validation suite:")
    run([sys.executable, "scripts/validate_json.py"])
    run([sys.executable, "scripts/validate_air_fixtures.py"])
    run([sys.executable, "scripts/validate_evidence_fixtures.py"])
    run([sys.executable, "scripts/validate_replay_contracts.py"])
    run([sys.executable, "scripts/validate_adapter_fixtures.py"])

    print()
    print("Future commands, DO NOT RUN in rehearsal:")
    print('git tag -a v0.1.0-pre -m "CompText AIR v0.1.0-pre: Public Review Candidate"')
    print("git push origin v0.1.0-pre")
    print('gh release create v0.1.0-pre --title "CompText AIR v0.1.0-pre" --notes-file docs/RELEASE_NOTES_v0.1.0-pre.md --prerelease')
    print()
    print("SUCCESS: pre-tag rehearsal passed without creating tag or release")

if __name__ == "__main__":
    main()
