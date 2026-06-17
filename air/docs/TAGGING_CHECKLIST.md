# Tagging Checklist - v0.1.0-pre

This checklist defines the requirements and commands for preparing the `v0.1.0-pre` tag for CompText AIR.

## Pre-tag Validation

Run the following commands locally to ensure the repository is in a valid state:

```bash
# Validate all JSON syntax and schemas
python scripts/validate_json.py

# Validate AIR fixture integrity
python scripts/validate_air_fixtures.py

# Validate Evidence hash-chain integrity
python scripts/validate_evidence_fixtures.py

# Validate AIR-to-Evidence replay contract fulfillment
python scripts/validate_replay_contracts.py

# Validate Runtime adapter safety and boundaries
python scripts/validate_adapter_fixtures.py
```

## GitHub CI Check

Verify that the latest commit on `main` has passed all GitHub Actions:

- [ ] Go to: `https://github.com/ProfRandom92/comptext-air/actions`
- [ ] Confirm `Validate AIR` workflow is green for the current HEAD.

## Working Tree Check

Ensure the working tree is clean and no uncommitted changes exist:

```bash
git status
# Result must show: "nothing to commit, working tree clean"
```

## Metadata Check

Verify `PROJEKT.md` reflects the correct state:

- [ ] `CURRENT_PHASE: 11`
- [ ] `STATUS: phase-11-tag-preparation`
- [ ] `Current validated state` mentions Phase 11 preparation.

## Release Boundary Checklist

Confirm that no forbidden claims are made in the documentation or fixtures:

- [ ] No claim of provider runtime.
- [ ] No claim of production MCP support.
- [ ] No claim of hidden chain-of-thought capture.
- [ ] No claim of package publishing.
- [ ] No claim of legal/compliance/forensic assurance.
- [ ] v0.1.0-pre is clearly marked as pre-release / public review candidate.

## Generated Report Artifact Policy

- [ ] Ensure `reports/generated/` contains the latest deterministic reports.
- [ ] Verify no absolute local paths or secrets are in the reports.

## Future Actions (DO NOT RUN YET)

The following commands are for the actual tagging event, which is **not** performed during Phase 11.

### Git Tag Command

```bash
# DO NOT RUN YET
# git tag -a v0.1.0-pre -m "CompText AIR v0.1.0-pre: Public Review Candidate"
# git push origin v0.1.0-pre
```

### GitHub Release Command

```bash
# DO NOT RUN YET
# gh release create v0.1.0-pre --title "CompText AIR v0.1.0-pre" --notes-file docs/RELEASE_NOTES_v0.1.0-pre.md --prerelease
```
