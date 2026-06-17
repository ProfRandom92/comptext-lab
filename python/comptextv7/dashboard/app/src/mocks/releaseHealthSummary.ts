import type { ReleaseHealthSummary } from '../types/domain';

export const releaseHealthSummaryFallback: ReleaseHealthSummary = {
  overall_status: 'unknown',
  checks: {
    contract_validation_report: {
      description: 'Contract schema validation report.',
      key: 'contract_validation_report',
      path: 'docs/reports/contract-validation-report.md',
      present: false,
      required: true,
      status: 'unavailable',
    },
    api_export_validation_report: {
      description: 'Synthetic API/export contract validation report.',
      key: 'api_export_validation_report',
      path: 'docs/reports/api-export-validation-report.md',
      present: false,
      required: true,
      status: 'unavailable',
    },
    project_health_report: {
      description: 'Generated project health and release status report.',
      key: 'project_health_report',
      path: 'docs/reports/project-health-report.md',
      present: false,
      required: true,
      status: 'unavailable',
    },
  },
  missing_artifacts: {
    required_local: ['docs/reports/dashboard-health-summary.json'],
    optional_cross_repo: [],
  },
  next_recommended_actions: [
    'Generate docs/reports/dashboard-health-summary.json before release review.',
    'Run the dashboard with a built static bundle or local backend route that can serve the summary artifact.',
  ],
  safety_notes: [
    'Health summary unavailable; showing synthetic fallback metadata only.',
    'No real Daimler data, customer payloads, secrets, cookies, tokens, raw production logs, or proprietary documents are included.',
  ],
  synthetic: true,
  summary_type: 'dashboard_release_health_fallback',
};
