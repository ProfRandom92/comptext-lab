import { AlertTriangle, CheckCircle2, FileJson, GitBranch, ShieldCheck } from 'lucide-react';
import { RELEASE_HEALTH_SUMMARY_PATH } from '../../lib/releaseHealth';
import type { ReleaseHealthState } from '../../lib/releaseHealth';
import type { ReleaseHealthCheck, ReleaseHealthStatus, ReleaseHealthSummary } from '../../types/domain';

function healthTone(status?: ReleaseHealthStatus) {
  const normalized = String(status ?? 'unknown').toLowerCase();
  if (['green', 'pass', 'passed', 'present', 'nominal', 'ok'].includes(normalized)) return 'nominal';
  if (['yellow', 'warning', 'degraded', 'missing_optional'].includes(normalized)) return 'warning';
  if (['red', 'fail', 'failed', 'critical', 'missing', 'unavailable'].includes(normalized)) return 'critical';
  return 'unknown';
}

function statusLabel(status?: ReleaseHealthStatus) {
  return String(status ?? 'unknown').replaceAll('_', ' ');
}

function checkStatus(check?: ReleaseHealthCheck) {
  if (!check) return 'unknown';
  if (check.status) return check.status;
  return check.present ? 'present' : 'missing';
}

function artifactList(artifacts?: string[]) {
  return artifacts && artifacts.length ? artifacts : ['None reported'];
}

function requiredChecks(summary?: ReleaseHealthSummary) {
  const checks = summary?.checks ?? {};
  return [
    ['Project health report', checks.project_health_report],
    ['Contract validation report', checks.contract_validation_report],
    ['API/export validation report', checks.api_export_validation_report],
    ['Contract fixture generation report', checks.contract_fixture_generation_report],
    ['Cross-repo release checklist', checks.cross_repo_release_checklist],
  ] satisfies Array<[string, ReleaseHealthCheck | undefined]>;
}

function readinessCopy(summary?: ReleaseHealthSummary, unavailable?: boolean) {
  if (unavailable) return 'Fallback mode: dashboard is rendering synthetic release-health metadata because the summary artifact is unavailable.';
  const status = String(summary?.overall_status ?? 'unknown').toLowerCase();
  if (status === 'green') return 'Ready for review: all required local validation artifacts are present.';
  if (status === 'yellow') return 'Review required: local validation is available, but optional/cross-repo promotion artifacts need attention.';
  if (status === 'red') return 'Blocked: required local validation artifacts are missing.';
  return 'Unknown readiness: regenerate the dashboard health summary before release review.';
}

function StatusPill({ status }: { status?: ReleaseHealthStatus }) {
  return <span className={`badge ${healthTone(status)}`}>{statusLabel(status)}</span>;
}

function SummaryHero({ summary, unavailable, message }: { summary?: ReleaseHealthSummary; unavailable?: boolean; message?: string }) {
  const status = summary?.overall_status ?? 'unknown';
  return (
    <section className={`release-hero ${healthTone(status)}`}>
      <div>
        <p className="eyebrow">Release readiness</p>
        <h3>{statusLabel(status)}</h3>
        <p>{readinessCopy(summary, unavailable)}</p>
        {message ? <p className="release-message"><AlertTriangle size={16} /> {message}</p> : null}
      </div>
      <div className="release-hero-meta">
        <StatusPill status={status} />
        <span>synthetic: {summary?.synthetic === false ? 'false' : 'true'}</span>
        <span>generated: {summary?.generated_at ?? 'static fallback'}</span>
        <span>source: {RELEASE_HEALTH_SUMMARY_PATH}</span>
      </div>
    </section>
  );
}

function CheckMatrix({ summary }: { summary?: ReleaseHealthSummary }) {
  return (
    <article className="card">
      <div className="card-header">
        <div>
          <h3>Release readiness matrix</h3>
          <p>Required local validation artifacts and their dashboard-facing status.</p>
        </div>
        <span className="badge medium"><ShieldCheck size={14} /> checks</span>
      </div>
      <div className="release-matrix">
        {requiredChecks(summary).map(([label, check]) => {
          const status = checkStatus(check);
          return (
            <div key={label} className="release-matrix-row">
              <div>
                <strong>{label}</strong>
                <p>{check?.path ?? check?.description ?? 'No artifact path reported'}</p>
              </div>
              <StatusPill status={status} />
            </div>
          );
        })}
      </div>
    </article>
  );
}

function ArtifactPanel({ title, artifacts, tone = 'medium' }: { title: string; artifacts?: string[]; tone?: string }) {
  return (
    <article className="card release-list-card">
      <div className="card-header">
        <div>
          <h3>{title}</h3>
          <p>Generated or expected release-review artifacts.</p>
        </div>
        <span className={`badge ${tone}`}>{artifactList(artifacts).length}</span>
      </div>
      <ul className="release-list">{artifactList(artifacts).map((artifact) => <li key={artifact}>{artifact}</li>)}</ul>
    </article>
  );
}

function GuidancePanel({ title, items, icon: Icon }: { title: string; items?: string[]; icon: typeof CheckCircle2 }) {
  return (
    <article className="card release-list-card">
      <div className="card-header">
        <div>
          <h3>{title}</h3>
          <p>Reviewer guidance surfaced from the release-health contract.</p>
        </div>
        <span className="badge medium"><Icon size={14} /></span>
      </div>
      <ul className="release-list">{artifactList(items).map((item) => <li key={item}>{item}</li>)}</ul>
    </article>
  );
}

export function ReleaseHealthPage({ state, isLoading = false }: { state?: ReleaseHealthState; isLoading?: boolean }) {
  if (isLoading && !state) {
    return <div className="loading"><span className="skeleton" /><p>Loading release health summary…</p></div>;
  }

  const summary = state?.summary;
  const missingRequired = summary?.missing_artifacts?.required_local ?? [];
  const missingOptional = summary?.missing_artifacts?.optional_cross_repo ?? [];
  const missingArtifacts = [...missingRequired, ...missingOptional];

  return (
    <div className="grid release-health-page">
      <SummaryHero summary={summary} unavailable={state?.unavailable} message={state?.message} />
      <section className="grid cols-3 release-kpi-grid">
        <article className="card"><div className="card-header"><h3>Local artifacts</h3><span className="badge nominal"><FileJson size={14} /></span></div><div className="metric">{summary?.required_artifacts_present?.length ?? 0}</div><p>Required artifacts reported as present.</p></article>
        <article className="card"><div className="card-header"><h3>Missing artifacts</h3><span className={`badge ${missingArtifacts.length ? 'warning' : 'nominal'}`}><AlertTriangle size={14} /></span></div><div className="metric">{missingArtifacts.length}</div><p>Required plus optional/cross-repo gaps.</p></article>
        <article className="card"><div className="card-header"><h3>Promotion gate</h3><span className="badge medium"><GitBranch size={14} /></span></div><div className="metric">{summary?.summary_type?.includes('fallback') ? 'Hold' : 'Review'}</div><p>Use checklist before experiment-to-runtime promotion.</p></article>
      </section>
      <CheckMatrix summary={summary} />
      <section className="grid cols-2">
        <ArtifactPanel title="Present local artifacts" artifacts={summary?.required_artifacts_present} tone="nominal" />
        <ArtifactPanel title="Missing artifacts" artifacts={missingArtifacts} tone={missingArtifacts.length ? 'warning' : 'nominal'} />
      </section>
      <section className="grid cols-2">
        <GuidancePanel title="Next recommended actions" items={summary?.next_recommended_actions} icon={CheckCircle2} />
        <GuidancePanel title="Safety notes" items={summary?.safety_notes} icon={ShieldCheck} />
      </section>
    </div>
  );
}
