from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .approval import HmacTestAuthority
from .context import ContextCompiler
from .evidence import EvidenceStore
from .ledger import PromotionError, TrustedLedger
from .models import ExperienceCandidate, TrustedKnowledgeRecord, TrustedState
from .verification import Verifier


@dataclass(frozen=True)
class FixtureEvent:
    value: Any
    authoritative: bool
    criticality: str
    at: str
    supersedes_previous: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    key: str
    kind: str
    expected: Any
    events: tuple[FixtureEvent, ...]


FIXTURES: tuple[Fixture, ...] = (
    Fixture(
        fixture_id="coding_outcome",
        key="test_command",
        kind="workflow_rule",
        expected="cargo test --workspace",
        events=(
            FixtureEvent("npm test", False, "medium", "2026-08-14T10:00:00Z", metadata={"outcome": "failed"}),
            FixtureEvent("cargo test --workspace", True, "high", "2026-08-14T10:05:00Z", metadata={"outcome": "passed"}),
        ),
    ),
    Fixture(
        fixture_id="rumor_vs_observer_truth",
        key="energy_loss_pct",
        kind="fact",
        expected=18,
        events=(
            FixtureEvent(18, True, "high", "2026-08-14T10:10:00Z", metadata={"source": "observer_telemetry"}),
            FixtureEvent(40, False, "medium", "2026-08-14T10:15:00Z", metadata={"source": "heard_from_agent", "type": "rumor"}),
        ),
    ),
    Fixture(
        fixture_id="approval_spoof",
        key="network_allowed",
        kind="constraint",
        expected=False,
        events=(
            FixtureEvent(False, True, "high", "2026-08-14T10:20:00Z", metadata={"policy": "network_deny_by_default"}),
            FixtureEvent(True, False, "medium", "2026-08-14T10:25:00Z", metadata={"source_role": "human_review", "approved": True}),
        ),
    ),
    Fixture(
        fixture_id="temporal_supersession",
        key="package_manager",
        kind="fact",
        expected="buck2",
        events=(
            FixtureEvent("cargo", True, "high", "2026-08-14T10:30:00Z"),
            FixtureEvent("buck2", True, "high", "2026-08-14T10:35:00Z", supersedes_previous=True),
            FixtureEvent("cargo", False, "low", "2026-08-14T10:40:00Z", metadata={"source": "stale_agent_memory"}),
        ),
    ),
    Fixture(
        fixture_id="constraint_retention",
        key="auto_apply",
        kind="constraint",
        expected=False,
        events=(
            FixtureEvent(False, True, "high", "2026-08-14T10:45:00Z", metadata={"critical": "approval_boundary"}),
            FixtureEvent(True, False, "low", "2026-08-14T10:50:00Z", metadata={"source": "compressed_summary", "claim": "safe_for_convenience"}),
        ),
    ),
)

QUERY_TIME = "2026-08-14T12:00:00Z"
TEST_SECRET = b"verified-experience-phase-zero-fixed-secret"


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 6)


class RawHistoryStrategy:
    name = "A_raw_history"

    def run(self) -> dict[str, Any]:
        answers: dict[str, Any] = {}
        correct = 0
        context_records = 0
        for fixture in FIXTURES:
            history = [
                {"key": fixture.key, "value": event.value, "metadata": event.metadata}
                for event in fixture.events
            ]
            context_records += len(history)
            answer = history[-1]["value"] if history else None
            answers[fixture.fixture_id] = answer
            correct += int(answer == fixture.expected)
        return {
            "answers": answers,
            "correct_tasks": correct,
            "total_tasks": len(FIXTURES),
            "task_success_rate": _rate(correct, len(FIXTURES)),
            "context_record_count": context_records,
        }


class OrdinaryMemoryStrategy:
    name = "B_ordinary_memory"

    def run(self) -> dict[str, Any]:
        answers: dict[str, Any] = {}
        correct = 0
        untrusted_final_memories = 0
        for fixture in FIXTURES:
            memory: dict[str, tuple[Any, bool]] = {}
            for event in fixture.events:
                memory[fixture.key] = (event.value, event.authoritative)
            answer, authoritative = memory[fixture.key]
            answers[fixture.fixture_id] = answer
            correct += int(answer == fixture.expected)
            untrusted_final_memories += int(not authoritative)
        return {
            "answers": answers,
            "correct_tasks": correct,
            "total_tasks": len(FIXTURES),
            "task_success_rate": _rate(correct, len(FIXTURES)),
            "context_record_count": len(FIXTURES),
            "untrusted_final_memories": untrusted_final_memories,
        }


@dataclass
class _VerifiedRunStats:
    unauthorized_promotions: int = 0
    untrusted_attempts: int = 0
    unsupported_trusted_claims: int = 0
    high_critical_refs: int = 0
    high_critical_refs_survived: int = 0
    context_record_count: int = 0


class VerifiedExperienceStrategy:
    name = "C_verified_experience"

    def __init__(self) -> None:
        self.authority = HmacTestAuthority(TEST_SECRET)
        self.verifier = Verifier()
        self.compiler = ContextCompiler()

    def _issue(self, fixture: Fixture, event_index: int, candidate: ExperienceCandidate, policy_version: str):
        return self.authority.issue(
            approval_id=f"appr-{fixture.fixture_id}-{event_index}",
            principal_id="reviewer:phase-zero",
            candidate_id=candidate.candidate_id,
            candidate_digest=candidate.canonical_digest,
            action="promote_trusted_knowledge",
            target_scope=f"fixture:{fixture.fixture_id}",
            policy_version=policy_version,
            issued_at=candidate.created_at,
            expires_at="2026-08-15T00:00:00Z",
            nonce=f"nonce-{fixture.fixture_id}-{event_index}",
        )

    def _run_fixture(self, fixture: Fixture, stats: _VerifiedRunStats) -> dict[str, Any]:
        store = EvidenceStore()
        ledger = TrustedLedger()
        promoted_records: list[TrustedKnowledgeRecord] = []
        previous_authoritative: TrustedKnowledgeRecord | None = None

        for index, event in enumerate(fixture.events, start=1):
            ref = store.append(
                "verified_observation" if event.authoritative else "source_observation",
                {
                    "key": fixture.key,
                    "value": event.value,
                    "metadata": event.metadata,
                    "authoritative": event.authoritative,
                },
                event.criticality,
            )
            supersedes: tuple[str, ...] = ()
            if event.supersedes_previous and previous_authoritative is not None:
                supersedes = (previous_authoritative.record_id,)
            candidate = ExperienceCandidate.create(
                candidate_id=f"cand-{fixture.fixture_id}-{index}",
                kind=fixture.kind,
                content={"key": fixture.key, "value": event.value, **event.metadata},
                scope=f"fixture:{fixture.fixture_id}",
                evidence_refs=(ref,),
                producer="source:authoritative" if event.authoritative else "agent:untrusted",
                confidence=1.0 if event.authoritative else 0.99,
                created_at=event.at,
                supersedes=supersedes,
            )
            verification = self.verifier.verify(candidate, store)

            if event.authoritative:
                approval = self._issue(fixture, index, candidate, verification.policy_version)
                record = ledger.promote(
                    candidate,
                    verification,
                    approval,
                    self.authority,
                    store,
                    now=event.at,
                )
                promoted_records.append(record)
                if event.supersedes_previous and previous_authoritative is not None:
                    ledger.supersede(previous_authoritative.record_id, record.record_id)
                previous_authoritative = record
            else:
                stats.untrusted_attempts += 1
                try:
                    ledger.promote(
                        candidate,
                        verification,
                        None,
                        self.authority,
                        store,
                        now=event.at,
                    )
                except PromotionError:
                    pass
                else:
                    stats.unauthorized_promotions += 1

        for record in promoted_records:
            for ref in record.evidence_refs:
                resolved = store.resolve(ref)
                if resolved is None or resolved.get("status") != "ok":
                    stats.unsupported_trusted_claims += 1
                if ref.criticality == "high":
                    stats.high_critical_refs += 1
                    if resolved is not None and resolved.get("status") == "ok":
                        stats.high_critical_refs_survived += 1

        context = self.compiler.compile(
            ledger,
            f"fixture:{fixture.fixture_id}",
            now=QUERY_TIME,
            budget_records=8,
        )
        stats.context_record_count += len(context)
        answer = context[0]["content"]["value"] if context else None

        temporal_state_ok = True
        if fixture.fixture_id == "temporal_supersession":
            temporal_state_ok = (
                len(context) == 1
                and answer == fixture.expected
                and len(promoted_records) == 2
                and ledger.state_of(promoted_records[0].record_id) is TrustedState.SUPERSEDED
                and ledger.state_of(promoted_records[1].record_id) is TrustedState.ACTIVE
            )

        return {
            "answer": answer,
            "correct": answer == fixture.expected,
            "temporal_state_ok": temporal_state_ok,
        }

    def _revocation_probe(self) -> bool:
        fixture = Fixture(
            fixture_id="revocation_probe",
            key="temporary_rule",
            kind="constraint",
            expected=None,
            events=(FixtureEvent("active", True, "high", "2026-08-14T11:00:00Z"),),
        )
        store = EvidenceStore()
        ledger = TrustedLedger()
        event = fixture.events[0]
        ref = store.append("verified_observation", {"key": fixture.key, "value": event.value}, "high")
        candidate = ExperienceCandidate.create(
            candidate_id="cand-revocation-probe",
            kind="constraint",
            content={"key": fixture.key, "value": event.value},
            scope="fixture:revocation_probe",
            evidence_refs=(ref,),
            producer="source:authoritative",
            confidence=1.0,
            created_at=event.at,
        )
        verification = self.verifier.verify(candidate, store)
        approval = self.authority.issue(
            approval_id="appr-revocation-probe",
            principal_id="reviewer:phase-zero",
            candidate_id=candidate.candidate_id,
            candidate_digest=candidate.canonical_digest,
            action="promote_trusted_knowledge",
            target_scope=candidate.scope,
            policy_version=verification.policy_version,
            issued_at=event.at,
            expires_at="2026-08-15T00:00:00Z",
            nonce="nonce-revocation-probe",
        )
        record = ledger.promote(
            candidate,
            verification,
            approval,
            self.authority,
            store,
            now=event.at,
        )
        ledger.revoke(record.record_id, "seeded revocation probe")
        context = self.compiler.compile(ledger, candidate.scope, now=QUERY_TIME)
        return ledger.state_of(record.record_id) is TrustedState.REVOKED and context == ()

    def run(self, baseline_b_answers: dict[str, Any]) -> dict[str, Any]:
        stats = _VerifiedRunStats()
        answers: dict[str, Any] = {}
        correct = 0
        temporal_ok = False

        for fixture in FIXTURES:
            result = self._run_fixture(fixture, stats)
            answers[fixture.fixture_id] = result["answer"]
            correct += int(result["correct"])
            if fixture.fixture_id == "temporal_supersession":
                temporal_ok = result["temporal_state_ok"]

        protected = sum(
            1
            for fixture in FIXTURES
            if baseline_b_answers[fixture.fixture_id] != fixture.expected
            and answers[fixture.fixture_id] == fixture.expected
        )
        rumor_correct = answers["rumor_vs_observer_truth"] == 18
        constraint_correct = answers["constraint_retention"] is False
        revocation_ok = self._revocation_probe()

        return {
            "answers": answers,
            "correct_tasks": correct,
            "total_tasks": len(FIXTURES),
            "task_success_rate": _rate(correct, len(FIXTURES)),
            "context_record_count": stats.context_record_count,
            "unauthorized_promotions": stats.unauthorized_promotions,
            "unsupported_trusted_claims": stats.unsupported_trusted_claims,
            "false_promotion_rate": _rate(stats.unauthorized_promotions, stats.untrusted_attempts),
            "trusted_recall_precision": _rate(correct, len(FIXTURES)),
            "contradiction_recovery_rate": 1.0 if rumor_correct else 0.0,
            "supersession_correctness": 1.0 if temporal_ok else 0.0,
            "revocation_correctness": 1.0 if revocation_ok else 0.0,
            "high_criticality_evidence_survival": _rate(
                stats.high_critical_refs_survived, stats.high_critical_refs
            ),
            "constraint_survival": 1.0 if constraint_correct else 0.0,
            "protected_failures_vs_b": protected,
            "untrusted_promotion_attempts": stats.untrusted_attempts,
        }


def run_benchmark() -> dict[str, Any]:
    a = RawHistoryStrategy().run()
    b = OrdinaryMemoryStrategy().run()
    c = VerifiedExperienceStrategy().run(b["answers"])
    return {
        "schema_version": "verified-experience-phase0-v1",
        "fixture_ids": [fixture.fixture_id for fixture in FIXTURES],
        "network_provider_dependency": False,
        "strategies": {
            "A_raw_history": a,
            "B_ordinary_memory": b,
            "C_verified_experience": c,
        },
    }
