import {
  Activity,
  ArrowRight,
  Boxes,
  CheckCircle2,
  Cloud,
  FileJson,
  FileWarning,
  Gauge,
  GitBranch,
  Layers3,
  LockKeyhole,
  PlayCircle,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { BarChart } from '../../components/charts/BarChart';
import { compactNumber, ms, percent, ratio } from '../../lib/format';
import { RELEASE_HEALTH_SUMMARY_PATH } from '../../lib/releaseHealth';
import type { ReleaseHealthState } from '../../lib/releaseHealth';
import type { DashboardPayload, ReleaseHealthCheck, ReleaseHealthStatus, ServiceHealth } from '../../types/domain';

function MetricCard({ title, value, description, icon: Icon, tone = 'nominal' }: { title: string; value: string; description: string; icon: typeof Activity; tone?: string }) {
  return <article className="card metric-card"><div className="card-header"><div><h3>{title}</h3><p>{description}</p></div><span className={`badge ${tone}`}><Icon size={14} /></span></div><div className="metric">{value}</div></article>;
}

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

function ReleaseHealthSummaryCard({ state }: { state?: ReleaseHealthState }) {
  const summary = state?.summary;
  const missingRequired = summary?.missing_artifacts?.required_local ?? [];
  const missingOptional = summary?.missing_artifacts?.optional_cross_repo ?? [];
  const missingArtifacts = [...missingRequired, ...missingOptional];
  const contractStatus = checkStatus(summary?.checks?.contract_validation_report);
  const apiStatus = checkStatus(summary?.checks?.api_export_validation_report);
  const projectStatus = checkStatus(summary?.checks?.project_health_report);
  const overall = summary?.overall_status ?? 'unknown';

  return (
    <article className="card release-health-card">
      <div className="card-header">
        <div>
          <h3>Release health summary</h3>
          <p>Static release-readiness artifact for sanitized dashboard review.</p>
        </div>
        <span className={`badge ${healthTone(overall)}`}>{statusLabel(overall)}</span>
      </div>
      {state?.unavailable ? <div className="notice warning"><FileWarning size={16} /><span>{state.message ?? `Health summary unavailable. Expected ${RELEASE_HEALTH_SUMMARY_PATH}.`}</span></div> : null}
      {!summary ? <div className="notice warning"><FileWarning size={16} /><span>Health summary unavailable. Expected {RELEASE_HEALTH_SUMMARY_PATH}.</span></div> : null}
      <div className="release-health-checks" aria-label="Release health validation checks">
        <div><span>Contract validation</span><strong className={`badge ${healthTone(contractStatus)}`}>{statusLabel(contractStatus)}</strong></div>
        <div><span>API/export validation</span><strong className={`badge ${healthTone(apiStatus)}`}>{statusLabel(apiStatus)}</strong></div>
        <div><span>Project health report</span><strong className={`badge ${healthTone(projectStatus)}`}>{statusLabel(projectStatus)}</strong></div>
      </div>
      <div className="release-health-columns">
        <div>
          <h4>Missing artifacts</h4>
          <ul>{artifactList(missingArtifacts).map((artifact) => <li key={artifact}>{artifact}</li>)}</ul>
        </div>
        <div>
          <h4>Next actions</h4>
          <ul>{artifactList(summary?.next_recommended_actions).map((action) => <li key={action}>{action}</li>)}</ul>
        </div>
        <div>
          <h4>Safety notes</h4>
          <ul>{artifactList(summary?.safety_notes).map((note) => <li key={note}>{note}</li>)}</ul>
        </div>
      </div>
    </article>
  );
}

function ServiceList({ services }: { services: ServiceHealth[] }) {
  return <div className="status-panel">{services.map((service) => <div key={service.id} className="service"><div><strong>{service.name}</strong><p>{service.owner} · {service.domain} · queue {service.queue_depth}</p></div><span className={`badge ${service.status}`}>{service.status}</span></div>)}</div>;
}

const architectureLayers = [
  { title: 'Header inventory', copy: 'Run-level provenance, event counts, severity counts, top codes, and timestamp boundaries.', icon: FileJson },
  { title: 'Diagnostic families', copy: 'Module, code, severity, signatures, and field slots are grouped into inspectable families.', icon: Layers3 },
  { title: 'Temporal windows', copy: 'Burst shape and top time buckets preserve when repeated diagnostic families dominate.', icon: Activity },
  { title: 'Compact frame', copy: 'Deterministic KVTC transport payload for review, assistant, dashboard, audit, or CI handoff.', icon: Boxes },
];

const validationSteps = [
  'Replay validation workflow: pytest, deterministic replay, token telemetry, semantic forensic validation, benchmark replay, dashboard startup validation.',
  'Agent workflow checks: reports, contract schemas, API/export fixtures, project health, dashboard health, dashboard typecheck/build, release-health smoke coverage.',
  'hash-companion-validation: CFI-01/02/03 cloud CI result contract and artifact flow.',
];

const demoSteps = [
  'Frame the problem: repetitive structured diagnostics create context-window, latency, and review-noise pressure.',
  'Show the KVTC-V7 layers and retained severity, module, code, count, temporal, and metadata anchors.',
  'Read token reduction conservatively: lower token count is not a correctness proof.',
  'Inspect GitHub Actions and CFI artifacts for the reviewed commit instead of asking for local execution.',
];

function Hero({ payload, releaseHealth }: { payload: DashboardPayload; releaseHealth?: ReleaseHealthState }) {
  const overall = releaseHealth?.summary?.overall_status ?? 'unknown';
  return (
    <section className="showcase-hero" aria-labelledby="showcase-title">
      <div className="hero-orbit" aria-hidden="true"><span /><span /><span /></div>
      <div className="hero-content">
        <p className="eyebrow"><Sparkles size={15} /> Replay validation · cloud-first review</p>
        <h2 id="showcase-title">CompText V7 turns repetitive diagnostics into auditable KVTC frames.</h2>
        <p className="hero-copy">A reviewer dashboard for deterministic, lossy token reduction over structured synthetic diagnostics, focused on retained anchors, validation evidence, CI artifacts, and explicit scope boundaries.</p>
        <div className="hero-actions" aria-label="Validation highlights">
          <span><Cloud size={16} /> GitHub Actions is the evidence authority</span>
          <span><LockKeyhole size={16} /> No local demo execution required</span>
          <span><ShieldCheck size={16} /> No production or certification claim</span>
        </div>
      </div>
      <aside className="hero-panel" aria-label="Current evidence summary">
        <div><span>Release posture</span><strong className={`badge ${healthTone(overall)}`}>{statusLabel(overall)}</strong></div>
        <div><span>Reported token savings</span><strong>{percent(payload.audit_summary.fleet_token_savings)}</strong></div>
        <div><span>Replay stable</span><strong>{payload.replay.stable ? 'Yes' : 'No'}</strong></div>
        <div><span>Tokenizer</span><strong>{payload.audit_summary.tokenizer_version}</strong></div>
      </aside>
    </section>
  );
}

function ArchitectureOverview() {
  return (
    <section className="showcase-section">
      <div className="section-heading">
        <p className="eyebrow">Architecture overview</p>
        <h2>Layered cloud-first handoff, not a backend expansion.</h2>
        <p>Based on the repository’s KVTC-V7 concept: deterministic layered frames for compact downstream review while raw retention and validation evidence remain separate concerns.</p>
      </div>
      <div className="architecture-grid">
        {architectureLayers.map((layer, index) => <article className="architecture-card" key={layer.title}><div className="architecture-icon"><layer.icon size={20} /></div><span>0{index + 1}</span><h3>{layer.title}</h3><p>{layer.copy}</p></article>)}
      </div>
    </section>
  );
}

function ArtifactCards({ releaseHealth }: { releaseHealth?: ReleaseHealthState }) {
  const checks = releaseHealth?.summary?.checks ?? {};
  const required = releaseHealth?.summary?.required_artifacts_present ?? [];
  const cards = [
    { title: 'Contract validation', check: checks.contract_validation_report, copy: 'Schema and contract evidence for release review.' },
    { title: 'API/export validation', check: checks.api_export_validation_report, copy: 'Synthetic export/API contract artifact.' },
    { title: 'Project health', check: checks.project_health_report, copy: 'Generated project health and release status report.' },
    { title: 'CFI artifact flow', check: undefined, copy: 'Cloud CI summary/result JSON is display-only metadata for compact handoff.' },
  ];
  return (
    <section className="showcase-section">
      <div className="section-heading compact-heading">
        <p className="eyebrow">CI artifacts</p>
        <h2>Evidence is surfaced as artifacts, not local assumptions.</h2>
        <p>{required.length ? `${required.length} required local artifact(s) are reported present by the release-health summary.` : 'Required artifact presence is not reported by the loaded summary.'}</p>
      </div>
      <div className="artifact-grid">
        {cards.map((card) => {
          const status = checkStatus(card.check);
          return <article className="artifact-card" key={card.title}><div className="card-header"><div><h3>{card.title}</h3><p>{card.copy}</p></div><span className={`badge ${healthTone(status)}`}>{card.check ? statusLabel(status) : 'documented'}</span></div>{card.check?.path ? <p className="mono artifact-path">{card.check.path}</p> : <p className="mono artifact-path">reports/hash-chilli-cloud-ci-*.json</p>}</article>;
        })}
      </div>
    </section>
  );
}

function BenchmarkVisualization({ payload }: { payload: DashboardPayload }) {
  const compressionData = payload.benchmarks.map((row) => ({ label: row.name, value: row.reduction_percent, auxiliary: row.top_family_coverage }));
  return (
    <section className="grid cols-2 benchmark-section">
      <article className="card chart-card"><div className="card-header"><div><h3>Benchmark/token metrics visualization</h3><p>Bars show reported token reduction; amber dots show top-family coverage. Interpret both together.</p></div><span className="badge warning">not proof</span></div><BarChart data={compressionData} valueLabel={(value) => percent(value)} /></article>
      <article className="card lane-card"><div className="card-header"><div><h3>Benchmark lanes</h3><p>Repository payload values are presented without adding new claims.</p></div><span className="badge">reported</span></div>{payload.benchmarks.map((row) => <div className="lane-row" key={row.name}><div><strong>{row.name}</strong><p>{row.honest_expectation}</p></div><div><span>{ratio(row.compression_ratio)}</span><small>{compactNumber.format(row.lines_per_second)} lines/s · {ms(row.median_ms)}</small></div></div>)}</article>
    </section>
  );
}

function ValidationPipeline({ payload }: { payload: DashboardPayload }) {
  return (
    <section className="validation-panel">
      <div className="section-heading">
        <p className="eyebrow">Validation pipeline</p>
        <h2>Cloud evidence first; validation boundaries explicit.</h2>
        <p>Forensic gates, replay stability, token telemetry, benchmark replay, and dashboard health are positioned as review evidence for synthetic/static validation material.</p>
      </div>
      <div className="pipeline-rail">
        {validationSteps.map((step, index) => <article key={step}><span>{index + 1}</span><p>{step}</p></article>)}
      </div>
      <div className="grid cols-3">
        <MetricCard title="Forensic failures" value={String(payload.audit_summary.forensic_failures)} description="Reported semantic/anchor/safety gate failures" icon={ShieldCheck} tone={payload.audit_summary.forensic_failures ? 'critical' : 'nominal'} />
        <MetricCard title="Replay mismatches" value={String(payload.replay.mismatches)} description={`${payload.replay.passes} pass(es), ${payload.replay.corpus_size} corpus item(s)`} icon={GitBranch} tone={payload.replay.mismatches ? 'critical' : 'nominal'} />
        <MetricCard title="Compression P95" value={ms(payload.audit_summary.p95_compression_ms)} description="Gateway processing latency from loaded payload" icon={Gauge} tone={payload.audit_summary.p95_compression_ms > 900 ? 'warning' : 'nominal'} />
      </div>
    </section>
  );
}

function DemoWalkthrough() {
  return (
    <section className="showcase-section walkthrough-section">
      <div className="section-heading">
        <p className="eyebrow">Reviewer/demo walkthrough</p>
        <h2>A no-local-execution path for repository reviewers.</h2>
        <p>The walkthrough guides reviewers through docs, Actions, CFI contracts, artifact payloads, and limits without asking them to run scripts or mutate local state.</p>
      </div>
      <div className="walkthrough-grid">
        {demoSteps.map((step, index) => <article key={step}><PlayCircle size={18} /><span>Step {index + 1}</span><p>{step}</p>{index < demoSteps.length - 1 ? <ArrowRight className="walkthrough-arrow" size={18} /> : <CheckCircle2 className="walkthrough-arrow" size={18} />}</article>)}
      </div>
    </section>
  );
}

export function OverviewPage({ payload, releaseHealth }: { payload: DashboardPayload; releaseHealth?: ReleaseHealthState }) {
  return (
    <div className="showcase-page">
      <Hero payload={payload} releaseHealth={releaseHealth} />
      <section className="grid cols-4">
        <MetricCard title="Token savings" value={percent(payload.audit_summary.fleet_token_savings)} description="Reported by the loaded dashboard payload" icon={Gauge} />
        <MetricCard title="Validation posture" value={releaseHealth?.summary?.overall_status ? statusLabel(releaseHealth.summary.overall_status) : 'unknown'} description="Release-health artifact state" icon={ShieldCheck} tone={healthTone(releaseHealth?.summary?.overall_status)} />
        <MetricCard title="Replay stable" value={payload.audit_summary.replay_determinism ? 'Yes' : 'No'} description={`${payload.replay.passes} deterministic replay pass(es)`} icon={GitBranch} tone={payload.replay.stable ? 'nominal' : 'critical'} />
        <MetricCard title="Cloud-first model" value="CI" description="Review evidence comes from Actions/artifacts" icon={Cloud} />
      </section>
      <ArchitectureOverview />
      <ArtifactCards releaseHealth={releaseHealth} />
      <BenchmarkVisualization payload={payload} />
      <ValidationPipeline payload={payload} />
      <ReleaseHealthSummaryCard state={releaseHealth} />
      <section className="grid cols-2">
        <article className="card"><div className="card-header"><div><h3>Validation scope boundaries</h3><p>Designed to make safe wording visible during review.</p></div><span className="badge warning">scoped</span></div><ul className="readiness-list"><li>Validated in repo/CI: deterministic prototype surfaces, schemas, reports, cloud workflows, and synthetic/static artifacts.</li><li>Planned next: governed pilot data, benchmark baselines, promotion evidence, and stakeholder-specific scripts.</li><li>Not claimed: production deployment, real-fleet correctness, certification, lossless reconstruction, or local demo validation.</li></ul></article>
        <article className="card"><div className="card-header"><div><h3>Service dependency health</h3><p>Operational ownership, SLO posture, and queue pressure from loaded payload.</p></div><span className="badge degraded">{payload.audit_summary.degraded_services} degraded</span></div><ServiceList services={payload.services} /></article>
      </section>
      <DemoWalkthrough />
    </div>
  );
}
