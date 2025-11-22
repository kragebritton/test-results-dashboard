import type { Environment, ProjectOverview } from '../types'
import './SummaryGrid.css'

function formatDate(value: string | null) {
  if (!value) return 'No runs yet'
  try {
    return new Date(value).toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch (error) {
    return value
  }
}

type Props = {
  overview: ProjectOverview[]
  statusMessage: string | null
  environment: Environment
}

export function SummaryGrid({ overview, statusMessage, environment }: Props) {
  if (statusMessage) {
    return (
      <div className="panel summary-panel">
        <div className="summary-panel__context">
          <span className="tag">Environment: {environment.toUpperCase()}</span>
        </div>
        <p>{statusMessage}</p>
      </div>
    )
  }

  return (
    <div className="summary-grid">
      {overview.map((project) => (
        <article key={project.project} className={`summary-card summary-card--${project.status}`}>
          <header>
            <div>
              <p className="eyebrow">Project</p>
              <h3>{project.project}</h3>
              <span className="tag">Environment: {project.environment.toUpperCase()}</span>
            </div>
            <span className={`status status--${project.status}`}>
              {project.status === 'passed' && 'Healthy'}
              {project.status === 'failed' && 'Attention needed'}
              {project.status === 'unknown' && 'Awaiting data'}
            </span>
          </header>

          <dl className="summary-grid__meta">
            <div>
              <dt>Last run</dt>
              <dd>{formatDate(project.lastRun)}</dd>
            </div>
            <div>
              <dt>Latest build</dt>
              <dd>{project.latest ?? '—'}</dd>
            </div>
          </dl>

          <div className="summary-card__stats">
            <div>
              <p className="muted">Total</p>
              <strong>{project.statistics.total}</strong>
            </div>
            <div>
              <p className="muted">Passed</p>
              <strong>{project.statistics.passed}</strong>
            </div>
            <div>
              <p className="muted">Failed / Broken</p>
              <strong>{project.statistics.failed + project.statistics.broken}</strong>
            </div>
            <div>
              <p className="muted">Skipped</p>
              <strong>{project.statistics.skipped}</strong>
            </div>
          </div>

          {project.reportUrl ? (
            <a className="inline-link" href={project.reportUrl} target="_blank" rel="noreferrer">
              View latest report
            </a>
          ) : (
            <p className="muted">Upload a report to see details.</p>
          )}
        </article>
      ))}
    </div>
  )
}
