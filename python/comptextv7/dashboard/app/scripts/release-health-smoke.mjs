import assert from 'node:assert/strict';
import process from 'node:process';
import { renderToStaticMarkup } from 'react-dom/server';
import { createServer } from 'vite';

const overviewSnippets = [
  'Release health summary',
  'yellow',
  'Contract validation',
  'API/export validation',
  'Project health report',
  'None reported',
  'Review the synthetic release checklist before tagging.',
  'Synthetic/static fixtures only.',
];

const overviewFallbackSnippets = [
  'Release health summary',
  'Health summary unavailable. Expected docs/reports/dashboard-health-summary.json.',
  'unknown',
  'unavailable',
  'Generate docs/reports/dashboard-health-summary.json before release review.',
  'No real Daimler data, customer payloads, secrets, cookies, tokens, raw production logs, or proprietary documents are included.',
];

const releasePageSnippets = [
  'Release readiness',
  'Review required: local validation is available, but optional/cross-repo promotion artifacts need attention.',
  'Release readiness matrix',
  'Contract validation report',
  'API/export validation report',
  'Present local artifacts',
  'Missing artifacts',
  'Next recommended actions',
  'Safety notes',
  'Review the synthetic release checklist before tagging.',
];

const releasePageFallbackSnippets = [
  'Release readiness',
  'Fallback mode: dashboard is rendering synthetic release-health metadata because the summary artifact is unavailable.',
  'Health summary unavailable. Expected docs/reports/dashboard-health-summary.json.',
  'unknown',
  'unavailable',
  'Generate docs/reports/dashboard-health-summary.json before release review.',
  'No real Daimler data, customer payloads, secrets, cookies, tokens, raw production logs, or proprietary documents are included.',
];

function assertIncludes(markup, snippets, label) {
  for (const snippet of snippets) {
    assert.ok(
      markup.includes(snippet),
      `${label} markup should include ${JSON.stringify(snippet)}. Rendered markup:\n${markup}`,
    );
  }
}

let server;
try {
  server = await createServer({
    appType: 'custom',
    logLevel: 'error',
    optimizeDeps: { noDiscovery: true },
    server: { middlewareMode: true },
  });

  const React = (await import('react')).default;
  const { OverviewPage } = await server.ssrLoadModule('/src/features/overview/OverviewPage.tsx');
  const { ReleaseHealthPage } = await server.ssrLoadModule('/src/features/release-health/ReleaseHealthPage.tsx');
  const { fallbackPayload } = await server.ssrLoadModule('/src/mocks/fallbackPayload.ts');
  const { releaseHealthSummaryFallback } = await server.ssrLoadModule('/src/mocks/releaseHealthSummary.ts');

  const healthySummary = {
    overall_status: 'yellow',
    checks: {
      contract_validation_report: { status: 'present', present: true, required: true, path: 'docs/reports/contract-validation-report.md' },
      api_export_validation_report: { status: 'present', present: true, required: true, path: 'docs/reports/api-export-validation-report.md' },
      project_health_report: { status: 'warning', present: true, required: true, path: 'docs/reports/project-health-report.md' },
      contract_fixture_generation_report: { status: 'present', present: true, required: true, path: 'docs/reports/contract-fixture-generation-report.md' },
      cross_repo_release_checklist: { status: 'present', present: true, required: true, path: 'docs/CROSS_REPO_RELEASE_CHECKLIST.md' },
    },
    required_artifacts_present: [
      'docs/reports/project-health-report.md',
      'docs/reports/contract-validation-report.md',
      'docs/reports/api-export-validation-report.md',
    ],
    missing_artifacts: {
      required_local: [],
      optional_cross_repo: [],
    },
    next_recommended_actions: [
      'Review the synthetic release checklist before tagging.',
      'Keep the release health summary attached to the dashboard review.',
    ],
    safety_notes: [
      'Synthetic/static fixtures only.',
      'No secrets, tokens, cookies, customer data, raw production logs, or proprietary documents are included.',
    ],
    synthetic: true,
    generated_at: '2026-01-01T00:00:00Z',
    summary_type: 'dashboard_release_health_smoke_fixture',
  };

  const healthyState = { summary: healthySummary, unavailable: false };
  const fallbackState = {
    summary: releaseHealthSummaryFallback,
    unavailable: true,
    message: 'Health summary unavailable. Expected docs/reports/dashboard-health-summary.json. 503 Service Unavailable',
  };

  const healthyMarkup = renderToStaticMarkup(
    React.createElement(OverviewPage, {
      payload: fallbackPayload,
      releaseHealth: healthyState,
    }),
  );
  assertIncludes(healthyMarkup, overviewSnippets, 'healthy release health overview smoke');

  const fallbackMarkup = renderToStaticMarkup(
    React.createElement(OverviewPage, {
      payload: fallbackPayload,
      releaseHealth: fallbackState,
    }),
  );
  assertIncludes(fallbackMarkup, overviewFallbackSnippets, 'fallback release health overview smoke');

  const releasePageMarkup = renderToStaticMarkup(React.createElement(ReleaseHealthPage, { state: healthyState }));
  assertIncludes(releasePageMarkup, releasePageSnippets, 'release health page smoke');

  const releaseFallbackMarkup = renderToStaticMarkup(React.createElement(ReleaseHealthPage, { state: fallbackState }));
  assertIncludes(releaseFallbackMarkup, releasePageFallbackSnippets, 'release health page fallback smoke');

  console.log('Release health dashboard smoke checks passed.');
} catch (error) {
  console.error('Release health dashboard smoke checks failed.');
  console.error(error);
  process.exitCode = 1;
} finally {
  if (server) await server.close();
}
