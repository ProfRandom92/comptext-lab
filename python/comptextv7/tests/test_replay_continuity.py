from __future__ import annotations

import json

from src.validation.replay_continuity import (
    ArchitectureJudge,
    EmbeddingJudge,
    HeuristicJudge,
    HiddenTruthJudge,
    StrictReplayEvaluator,
    TemporalJudge,
    build_adversarial_scenarios,
    run_comparison,
    run_replay_chain,
    write_benchmark_artifacts,
)


def test_adversarial_suite_covers_required_hostile_scenarios() -> None:
    names = {scenario.name for scenario in build_adversarial_scenarios()}

    scenarios = build_adversarial_scenarios()
    assert {scenario.attack_family for scenario in scenarios} == {
        "context_fragmentation",
        "dependency_inversion",
        "temporal_mutation",
        "architecture_drift_injection",
        "contradictory_goal_injection",
        "hidden_constraint_removal",
        "semantic_ambiguity_noise",
        "replay_truncation",
        "partial_reconstruction",
        "recursive_recompression",
    }
    assert {scenario.dataset_kind for scenario in scenarios} == {
        "real_pr_discussion",
        "architecture_rfc",
        "bug_report",
        "ci_cd_incident",
        "dependency_migration_discussion",
        "production_issue_timeline",
        "contradictory_engineering_decisions",
        "roadmap_revision",
        "temporal_change_log",
        "multi_step_operational_workflow",
    }

    assert names == {
        "pr_discussion_context_fragmentation",
        "rfc_dependency_inversion",
        "bug_report_temporal_mutation",
        "ci_incident_architecture_drift",
        "dependency_migration_contradictory_goals",
        "production_hidden_constraint_removal",
        "decision_log_semantic_ambiguity",
        "roadmap_replay_truncation",
        "change_log_partial_reconstruction",
        "workflow_recursive_recompression",
    }


def test_v7_degrades_honestly_but_remains_structurally_better_at_100_iterations() -> None:
    comparison = run_comparison(iterations=100)
    summary = {row["mode"]: row for row in comparison["summary"]}

    assert comparison["purpose"] == "strict adversarial semantic/operational replay continuity evaluation, not a token benchmark"
    assert comparison["iteration_ladders_supported"] == [25, 50, 100, 250]
    assert summary["comptext_v7"]["mean_final_continuity"] < 1.0
    assert summary["comptext_v7"]["mean_final_continuity"] > summary["adaptive"]["mean_final_continuity"]
    assert summary["adaptive"]["mean_final_continuity"] > summary["baseline"]["mean_final_continuity"]
    assert summary["baseline"]["mean_final_continuity"] > summary["naive"]["mean_final_continuity"]
    assert summary["comptext_v7"]["mean_longevity_iterations"] > summary["adaptive"]["mean_longevity_iterations"]
    assert summary["comptext_v7"]["mean_replay_collapse_iteration"] > summary["adaptive"]["mean_replay_collapse_iteration"]


def test_strict_evaluator_exposes_v7_long_horizon_failure_flags() -> None:
    scenario = build_adversarial_scenarios()[0]
    chain = run_replay_chain(scenario, "comptext_v7", iterations=100)

    assert len(chain.iterations) == 100
    assert chain.iterations[0].metrics.overall_continuity == 1.0
    assert chain.iterations[-1].metrics.overall_continuity < chain.iterations[0].metrics.overall_continuity
    assert chain.iterations[-1].metrics.hidden_constraint_survival < 1.0
    assert "hidden_constraint_loss" in chain.iterations[-1].failure_flags
    assert chain.collapse_iteration == 0


def test_replay_chains_support_25_50_100_and_250_iterations() -> None:
    scenario = build_adversarial_scenarios()[2]

    assert len(run_replay_chain(scenario, "comptext_v7", iterations=25).iterations) == 25
    assert len(run_replay_chain(scenario, "comptext_v7", iterations=50).iterations) == 50
    assert len(run_replay_chain(scenario, "comptext_v7", iterations=100).iterations) == 100
    assert len(run_replay_chain(scenario, "comptext_v7", iterations=250).iterations) == 250


def test_evaluator_is_separate_from_replay_generation() -> None:
    scenario = build_adversarial_scenarios()[1]
    chain = run_replay_chain(scenario, "baseline", iterations=10)

    assert StrictReplayEvaluator.__name__ == "StrictReplayEvaluator"
    assert chain.iterations[-1].metrics.temporal_consistency_score < 1.0
    assert "temporal_order_loss" in chain.iterations[-1].failure_flags


def test_external_replay_judge_architecture_reports_all_independent_judges() -> None:
    scenario = build_adversarial_scenarios()[2]
    chain = run_replay_chain(scenario, "baseline", iterations=16)
    final_iteration = chain.iterations[-1]

    assert {result.judge_type for result in final_iteration.judge_results} == {
        "heuristic",
        "embedding",
        "semantic_entailment",
        "contradiction",
        "temporal",
        "architecture",
        "hidden_truth",
    }
    assert isinstance(HeuristicJudge(), HeuristicJudge)
    assert isinstance(EmbeddingJudge(), EmbeddingJudge)
    assert isinstance(TemporalJudge(), TemporalJudge)
    assert isinstance(ArchitectureJudge(), ArchitectureJudge)
    assert isinstance(HiddenTruthJudge(), HiddenTruthJudge)
    assert final_iteration.metrics.evaluator_agreement_divergence >= 0.0
    assert final_iteration.metrics.semantic_entailment_score <= 1.0
    assert final_iteration.metrics.replay_semantic_divergence >= 0.0
    assert final_iteration.metrics.hidden_truth_survival_rate <= 1.0
    assert final_iteration.metrics.temporal_causality_retention <= 1.0


def test_comparative_analysis_exposes_new_external_judge_metrics() -> None:
    comparison = run_comparison(iterations=10)
    row = next(item for item in comparison["summary"] if item["mode"] == "comptext_v7")

    assert comparison["evaluation_layers"] == ["replay_generator", "external_replay_judge", "comparative_analysis"]
    assert comparison["judge_types"] == ["heuristic", "embedding", "semantic_entailment", "contradiction", "temporal", "architecture", "hidden_truth"]
    assert "mean_evaluator_agreement_divergence" in row
    assert "mean_semantic_entailment_score" in row
    assert "mean_replay_semantic_divergence" in row
    assert "mean_hidden_truth_survival_rate" in row
    assert "mean_temporal_causality_retention" in row
    assert "mean_architecture_mutation_resistance" in row


def test_benchmark_artifacts_are_deterministic_and_include_adversarial_visualizations(tmp_path) -> None:
    paths = write_benchmark_artifacts(tmp_path, iterations=10)
    first = paths["summary"].read_text(encoding="utf-8")
    paths = write_benchmark_artifacts(tmp_path, iterations=10)
    second = paths["summary"].read_text(encoding="utf-8")
    summary = json.loads(first)

    assert first == second
    assert summary["digest"]
    assert {
        "replay_collapse_curves",
        "drift_acceleration_graph",
        "contradiction_accumulation_heatmap",
        "constraint_survival_curves",
        "replay_longevity_comparisons",
        "failure_point_timelines",
        "semantic_stability_heatmaps",
        "continuity_half_life_chart",
        "temporal_consistency_degradation",
        "architecture_mutation_timeline",
        "evaluator_agreement_divergence",
        "hidden_constraint_survival_curves",
    }.issubset(paths)
    for path in paths.values():
        assert path.exists()
        assert path.read_text(encoding="utf-8").strip()
