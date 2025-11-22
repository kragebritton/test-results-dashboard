import { useMemo, useState } from 'react'
import type { Environment, ProjectOverview } from '../types'
import '../styles/table.css'

type Props = {
  overview: ProjectOverview[]
  statusMessage: string | null
  environment: Environment
}

type StatusVariant = {
  label: string
  tone: 'success' | 'warning' | 'danger' | 'muted'
}

const statusVariants: Record<ProjectOverview['status'] | 'flaky', StatusVariant> = {
  passed: { label: 'Passing', tone: 'success' },
  failed: { label: 'Failing', tone: 'danger' },
  unknown: { label: 'Unknown', tone: 'muted' },
  flaky: { label: 'Flaky', tone: 'warning' },
}

function getStatusVariant(status: ProjectOverview['status'] | 'flaky'): StatusVariant {
  return statusVariants[status] ?? statusVariants.unknown
}

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

export function ProjectTable({ overview, statusMessage, environment }: Props) {
  const [rowsPerPage, setRowsPerPage] = useState(8)
  const [page, setPage] = useState(0)

  const rows = useMemo(() => overview, [overview])
  const totalPages = Math.max(1, Math.ceil(rows.length / rowsPerPage))
  const clampedPage = Math.min(page, totalPages - 1)
  const pageStart = clampedPage * rowsPerPage
  const pageRows = rows.slice(pageStart, pageStart + rowsPerPage)

  const handleRowsPerPageChange = (value: number) => {
    setRowsPerPage(value)
    setPage(0)
  }

  const handleRowActivate = (url: string | null) => {
    if (url) {
      window.open(url, '_blank', 'noopener')
    }
  }

  return (
    <section className="table-card" aria-label="Project overview">
      <header className="table-card__header">
        <div>
          <p className="eyebrow">Projects overview</p>
          <h2>Latest builds and health</h2>
          <p className="muted">Keep tabs on project status, latest builds, and quick actions.</p>
        </div>
        <div className="table-card__cta">
          <button type="button" className="button button--primary">
            Add Project
          </button>
        </div>
      </header>

      <div className="table-card__body">
        <div className="table-card__context">
          <span className="tag">Environment: {environment.toUpperCase()}</span>
        </div>

        {statusMessage ? (
          <div className="empty-table">{statusMessage}</div>
        ) : (
          <div className="table-container">
            <table className="projects-table">
              <thead>
                <tr>
                  <th scope="col">Project</th>
                  <th scope="col">Status</th>
                  <th scope="col">Latest Build</th>
                  <th scope="col">Last Run</th>
                  <th scope="col">Environment</th>
                  <th scope="col" className="cell--numeric">
                    Total
                  </th>
                  <th scope="col" className="cell--numeric">
                    Passed
                  </th>
                  <th scope="col" className="cell--numeric">
                    Failed
                  </th>
                  <th scope="col" className="cell--numeric">
                    Skipped
                  </th>
                  <th scope="col" className="cell--actions">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {pageRows.map((project) => {
                  const statusVariant = getStatusVariant(project.status)
                  const isClickable = Boolean(project.reportUrl)
                  const failedTotal = project.statistics.failed + project.statistics.broken

                  return (
                    <tr
                      key={project.project}
                      className={isClickable ? 'is-clickable' : undefined}
                      onClick={() => handleRowActivate(project.reportUrl)}
                      onKeyDown={(event) => {
                        if (isClickable && (event.key === 'Enter' || event.key === ' ')) {
                          event.preventDefault()
                          handleRowActivate(project.reportUrl)
                        }
                      }}
                      role={isClickable ? 'button' : undefined}
                      tabIndex={isClickable ? 0 : undefined}
                    >
                      <td className="cell--truncate" title={project.project}>
                        <div className="cell-stack">
                          <span className="cell-title">{project.project}</span>
                          {project.latest && <span className="cell-subtitle">Build {project.latest}</span>}
                        </div>
                      </td>
                      <td>
                        <span className={`status-badge status-badge--${statusVariant.tone}`}>
                          {statusVariant.label}
                        </span>
                      </td>
                      <td className="cell--truncate" title={project.latest ?? 'No builds yet'}>
                        {project.latest ?? '—'}
                      </td>
                      <td className="cell--truncate" title={formatDate(project.lastRun)}>
                        {formatDate(project.lastRun)}
                      </td>
                      <td className="cell--truncate" title={project.environment.toUpperCase()}>
                        {project.environment.toUpperCase()}
                      </td>
                      <td className="cell--numeric">{project.statistics.total}</td>
                      <td className="cell--numeric success">{project.statistics.passed}</td>
                      <td className="cell--numeric danger">{failedTotal}</td>
                      <td className="cell--numeric muted">{project.statistics.skipped}</td>
                      <td className="cell--actions">
                        <div className="actions">
                          <button
                            type="button"
                            className="icon-button"
                            title={project.reportUrl ? 'View report details' : 'No report available'}
                            aria-label="View report details"
                            disabled={!project.reportUrl}
                            onClick={(event) => {
                              event.stopPropagation()
                              handleRowActivate(project.reportUrl)
                            }}
                          >
                            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                              <path d="M12 5c-7 0-11 7-11 7s4 7 11 7 11-7 11-7-4-7-11-7Zm0 12a5 5 0 1 1 0-10 5 5 0 0 1 0 10Zm0-2.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z" />
                            </svg>
                          </button>
                          <button
                            type="button"
                            className="icon-button"
                            title="Trigger rerun (coming soon)"
                            aria-label="Trigger rerun"
                            disabled
                            onClick={(event) => event.stopPropagation()}
                          >
                            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                              <path d="M12 5a7 7 0 0 1 6.32 4H16v2h6V5h-2v2.26A9 9 0 0 0 3 12h2a7 7 0 0 1 7-7Zm-6.32 8A7 7 0 0 0 12 19a7 7 0 0 0 6-3.32V19h2v-6h-6v2h2.58A5 5 0 0 1 12 17a5 5 0 0 1-4.9-4H5.68Z" />
                            </svg>
                          </button>
                          <button
                            type="button"
                            className="icon-button icon-button--danger"
                            title="Delete project (disabled)"
                            aria-label="Delete project"
                            disabled
                            onClick={(event) => event.stopPropagation()}
                          >
                            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                              <path d="M9 4h6l1 2h5v2h-2v11a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V8H3V6h5l1-2Zm8 4H7v10h10V8Zm-6 2v6H9v-6h2Zm4 0v6h-2v-6h2Zm-6.62-4-.34.69H16.2l-.34-.69H9.38Z" />
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <footer className="table-card__footer">
        <div className="pagination">
          <div className="pagination__rows">
            <label htmlFor="rows-per-page">Rows per page</label>
            <select
              id="rows-per-page"
              value={rowsPerPage}
              onChange={(event) => handleRowsPerPageChange(Number(event.target.value))}
            >
              {[5, 8, 10, 20].map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
          <div className="pagination__controls">
            <span className="pagination__info">
              Page {clampedPage + 1} of {totalPages}
            </span>
            <div className="pagination__buttons">
              <button
                type="button"
                className="icon-button"
                onClick={() => setPage((prev) => Math.max(0, prev - 1))}
                disabled={clampedPage === 0}
                aria-label="Previous page"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path d="M15.41 7.41 14 6l-6 6 6 6 1.41-1.41L10.83 12l4.58-4.59Z" />
                </svg>
              </button>
              <button
                type="button"
                className="icon-button"
                onClick={() => setPage((prev) => Math.min(totalPages - 1, prev + 1))}
                disabled={clampedPage >= totalPages - 1}
                aria-label="Next page"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path d="M8.59 16.59 10 18l6-6-6-6-1.41 1.41L13.17 12l-4.58 4.59Z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </footer>
    </section>
  )
}
