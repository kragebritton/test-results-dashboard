import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { fetchProjectOverview, fetchProjects } from './api'
import { ProjectList } from './components/ProjectList'
import { ProjectTable } from './components/ProjectTable'
import { ReportFrame } from './components/ReportFrame'
import { SummaryGrid } from './components/SummaryGrid'
import type { Environment, ProjectOverview, ProjectSummary } from './types'
import './styles/layout.css'
import './styles/table.css'
import './styles/home.css'

type SortKey = 'project' | 'branch' | 'lastRun' | 'status' | 'duration'
type SortDirection = 'asc' | 'desc'
type StatusFilter = 'all' | 'passing' | 'failing' | 'flaky'
type ScopeFilter = 'my-projects' | 'favorites' | 'recent'
type ViewMode = 'summary' | 'reports' | 'settings'

type ProjectConfig = {
  name: string
  reportUrl: string
  description: string
  environment: Environment
}

type SortState = { key: SortKey; direction: SortDirection }

type DerivedOverview = ProjectOverview & {
  branchLabel: string
  durationMs?: number
  derivedStatus: StatusFilter
}

const PREFERENCE_KEY = 'trd-table-preferences'
const DEFAULT_ENV_KEY = 'trd-default-environment'
const CONFIG_KEY = 'trd-project-configs'

function formatDateTime(value: string | null) {
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

function formatDuration(milliseconds: number | null | undefined) {
  if (!milliseconds || Number.isNaN(milliseconds)) return '—'
  const seconds = milliseconds / 1000
  if (seconds < 90) return `${seconds.toFixed(1)}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)
  return `${minutes}m ${remainingSeconds}s`
}

function getInitialPreferences(): {
  searchQuery: string
  statusFilter: StatusFilter
  scopeFilter: ScopeFilter
  sort: SortState
  dateFrom: string
  dateTo: string
} {
  const defaultPrefs: {
    searchQuery: string
    statusFilter: StatusFilter
    scopeFilter: ScopeFilter
    sort: SortState
    dateFrom: string
    dateTo: string
  } = {
    searchQuery: '',
    statusFilter: 'all',
    scopeFilter: 'my-projects',
    sort: { key: 'project', direction: 'asc' },
    dateFrom: '',
    dateTo: '',
  }

  const params = new URLSearchParams(window.location.search)
  const stored = localStorage.getItem(PREFERENCE_KEY)
  const storedPrefs = stored ? JSON.parse(stored) : {}

  const validStatus = ['all', 'passing', 'failing', 'flaky'] satisfies StatusFilter[]
  const validScope = ['my-projects', 'favorites', 'recent'] satisfies ScopeFilter[]
  const validSortKey = ['project', 'branch', 'lastRun', 'status', 'duration'] satisfies SortKey[]
  const validSortDir = ['asc', 'desc'] satisfies SortDirection[]

  const statusParam = params.get('status')
  const scopeParam = params.get('scope')
  const sortKeyParam = params.get('sortKey')
  const sortDirParam = params.get('sortDir')

  return {
    searchQuery: params.get('q') ?? storedPrefs.searchQuery ?? defaultPrefs.searchQuery,
    statusFilter:
      (statusParam && validStatus.includes(statusParam as StatusFilter) && (statusParam as StatusFilter)) ||
      storedPrefs.statusFilter ||
      defaultPrefs.statusFilter,
    scopeFilter:
      (scopeParam && validScope.includes(scopeParam as ScopeFilter) && (scopeParam as ScopeFilter)) ||
      storedPrefs.scopeFilter ||
      defaultPrefs.scopeFilter,
    sort:
      sortKeyParam && sortDirParam && validSortKey.includes(sortKeyParam as SortKey) && validSortDir.includes(sortDirParam as SortDirection)
        ? { key: sortKeyParam as SortKey, direction: sortDirParam as SortDirection }
        : storedPrefs.sort ?? defaultPrefs.sort,
    dateFrom: params.get('from') ?? storedPrefs.dateFrom ?? defaultPrefs.dateFrom,
    dateTo: params.get('to') ?? storedPrefs.dateTo ?? defaultPrefs.dateTo,
  }
}

function App() {
  const initialPreferences = useMemo(() => getInitialPreferences(), [])
  const storedEnvironment = (localStorage.getItem(DEFAULT_ENV_KEY) as Environment | null) ?? 'prod'
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [overview, setOverview] = useState<ProjectOverview[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [overviewLoading, setOverviewLoading] = useState(true)
  const [overviewError, setOverviewError] = useState<string | null>(null)
  const [selectedProject, setSelectedProject] = useState<ProjectSummary | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('summary')
  const [environment, setEnvironment] = useState<Environment>(storedEnvironment)
  const [sortState, setSortState] = useState<SortState>(initialPreferences.sort)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>(initialPreferences.statusFilter)
  const [scopeFilter, setScopeFilter] = useState<ScopeFilter>(initialPreferences.scopeFilter)
  const [searchQuery, setSearchQuery] = useState(initialPreferences.searchQuery)
  const [dateFrom, setDateFrom] = useState(initialPreferences.dateFrom)
  const [dateTo, setDateTo] = useState(initialPreferences.dateTo)
  const [favoriteProjects, setFavoriteProjects] = useState<string[]>(() => {
    const stored = localStorage.getItem('trd-favorites')
    return stored ? JSON.parse(stored) : []
  })
  const [sortAnnouncement, setSortAnnouncement] = useState('')
  const [projectConfigs, setProjectConfigs] = useState<ProjectConfig[]>(() => {
    const stored = localStorage.getItem(CONFIG_KEY)
    return stored ? JSON.parse(stored) : []
  })
  const [configForm, setConfigForm] = useState<ProjectConfig>({
    name: '',
    reportUrl: '',
    description: '',
    environment,
  })

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetchProjects(environment)
      .then((data) => {
        setProjects(data)
        setSelectedProject((current) => {
          if (current) {
            const matching = data.find((project) => project.project === current.project)
            if (matching) return matching
          }
          return data[0] ?? null
        })
      })
      .catch(() => setError('Unable to load projects. Please check the API service.'))
      .finally(() => setLoading(false))
  }, [environment])

  useEffect(() => {
    setOverviewLoading(true)
    setOverviewError(null)
    fetchProjectOverview(environment)
      .then((data) => setOverview(data))
      .catch(() => setOverviewError('Unable to load project overview. Please check the API service.'))
      .finally(() => setOverviewLoading(false))
  }, [environment])

  const handleSelect = (projectName: string) => {
    const target = projects.find((project) => project.project === projectName)
    if (target) setSelectedProject(target)
  }

  const handleEnvironmentChange = (envOption: Environment) => {
    setEnvironment(envOption)
    setConfigForm((current) => ({ ...current, environment: envOption }))
  }

  const handleSortChange = (key: SortKey) => {
    setSortState((current) => {
      const nextDirection: SortDirection = current.key === key && current.direction === 'asc' ? 'desc' : 'asc'
      const updated = { key, direction: nextDirection }
      setSortAnnouncement(`Sorted by ${key === 'lastRun' ? 'last run' : key} in ${nextDirection}ending order`)
      return updated
    })
  }

  const toggleFavorite = (projectName: string) => {
    setFavoriteProjects((current) =>
      current.includes(projectName) ? current.filter((name) => name !== projectName) : [...current, projectName],
    )
  }

  useEffect(() => {
    const prefs = {
      sort: sortState,
      statusFilter,
      scopeFilter,
      searchQuery,
      dateFrom,
      dateTo,
    }
    localStorage.setItem(PREFERENCE_KEY, JSON.stringify(prefs))

    const params = new URLSearchParams(window.location.search)
    params.set('sortKey', sortState.key)
    params.set('sortDir', sortState.direction)
    params.set('status', statusFilter)
    params.set('scope', scopeFilter)
    params.set('q', searchQuery)
    if (dateFrom) params.set('from', dateFrom)
    else params.delete('from')
    if (dateTo) params.set('to', dateTo)
    else params.delete('to')

    window.history.replaceState(null, '', `${window.location.pathname}?${params.toString()}`)
  }, [dateFrom, dateTo, scopeFilter, searchQuery, sortState, statusFilter])

  useEffect(() => {
    localStorage.setItem('trd-favorites', JSON.stringify(favoriteProjects))
  }, [favoriteProjects])

  useEffect(() => {
    localStorage.setItem(DEFAULT_ENV_KEY, environment)
  }, [environment])

  useEffect(() => {
    localStorage.setItem(CONFIG_KEY, JSON.stringify(projectConfigs))
  }, [projectConfigs])

  const statusMessage = useMemo(() => {
    if (loading) return 'Loading projects...'
    if (error) return error
    if (!projects.length) return 'No projects have been uploaded yet.'
    return null
  }, [loading, error, projects])

  const overviewMessage = useMemo(() => {
    if (overviewLoading) return 'Loading latest results...'
    if (overviewError) return overviewError
    if (!overview.length) return 'No projects have been uploaded yet.'
    return null
  }, [overview, overviewLoading, overviewError])

  const hasDates = useMemo(() => overview.some((item) => Boolean(item.lastRun)), [overview])

  const decoratedOverview: DerivedOverview[] = useMemo(
    () =>
      overview.map((item) => ({
        ...item,
        branchLabel: (item as { branch?: string }).branch ?? item.latest ?? '—',
        durationMs:
          (item as { durationMs?: number; duration?: number }).durationMs ?? (item as { duration?: number }).duration ?? undefined,
        derivedStatus: item.status === 'passed' ? 'passing' : item.status === 'failed' ? 'failing' : 'flaky',
      })),
    [overview],
  )

  const filteredOverview = useMemo(() => {
    const scoped = decoratedOverview.filter((item) => {
      if (scopeFilter === 'favorites') {
        return favoriteProjects.includes(item.project)
      }
      if (scopeFilter === 'recent') {
        if (!item.lastRun) return false
        const lastRunDate = new Date(item.lastRun).getTime()
        const fourteenDaysAgo = Date.now() - 14 * 24 * 60 * 60 * 1000
        return lastRunDate >= fourteenDaysAgo
      }
      return true
    })

    const statusScoped = statusFilter === 'all' ? scoped : scoped.filter((item) => item.derivedStatus === statusFilter)
    const searchValue = searchQuery.trim().toLowerCase()
    const searched = searchValue
      ? statusScoped.filter(
          (item) =>
            item.project.toLowerCase().includes(searchValue) ||
            item.branchLabel.toLowerCase().includes(searchValue) ||
            item.environment.toLowerCase().includes(searchValue),
        )
      : statusScoped

    const dateFiltered = searched.filter((item) => {
      if (!item.lastRun) return !(dateFrom || dateTo)
      const date = new Date(item.lastRun)
      if (Number.isNaN(date.getTime())) return true
      const afterFrom = dateFrom ? date >= new Date(`${dateFrom}T00:00:00`) : true
      const beforeTo = dateTo ? date <= new Date(`${dateTo}T23:59:59`) : true
      return afterFrom && beforeTo
    })

    return dateFiltered.sort((a, b) => {
      const directionMultiplier = sortState.direction === 'asc' ? 1 : -1
      switch (sortState.key) {
        case 'project':
          return a.project.localeCompare(b.project) * directionMultiplier
        case 'branch':
          return a.branchLabel.localeCompare(b.branchLabel) * directionMultiplier
        case 'status':
          return a.derivedStatus.localeCompare(b.derivedStatus) * directionMultiplier
        case 'duration':
          return ((a.durationMs ?? 0) - (b.durationMs ?? 0)) * directionMultiplier
        case 'lastRun':
        default: {
          const aTime = a.lastRun ? new Date(a.lastRun).getTime() : 0
          const bTime = b.lastRun ? new Date(b.lastRun).getTime() : 0
          return (aTime - bTime) * directionMultiplier
        }
      }
    })
  }, [decoratedOverview, scopeFilter, favoriteProjects, statusFilter, searchQuery, dateFrom, dateTo, sortState])

  const passingCount = decoratedOverview.filter((item) => item.derivedStatus === 'passing').length
  const failingCount = decoratedOverview.filter((item) => item.derivedStatus === 'failing').length
  const flakyCount = decoratedOverview.filter((item) => item.derivedStatus === 'flaky').length

  const handleConfigSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!configForm.name.trim() || !configForm.reportUrl.trim()) return

    setProjectConfigs((current) => {
      const existingIndex = current.findIndex(
        (entry) => entry.name.toLowerCase() === configForm.name.trim().toLowerCase(),
      )
      const updated = [...current]
      if (existingIndex >= 0) {
        updated[existingIndex] = { ...configForm, name: configForm.name.trim() }
      } else {
        updated.push({ ...configForm, name: configForm.name.trim() })
      }
      return updated
    })

    setConfigForm({ name: '', reportUrl: '', description: '', environment })
  }

  const handleConfigDelete = (name: string) => {
    setProjectConfigs((current) => current.filter((config) => config.name !== name))
  }

  return (
    <div className="layout">
      <header className="layout__header">
        <div className="layout__intro">
          <p className="eyebrow">QA / Test Engineering</p>
          <h1>Test Results Dashboard</h1>
          <p className="subtitle">
            Track pipelines, spot flaky suites, and configure project access from one place.
          </p>
          <div className="layout__cta">
            <a className="primary-cta" href="#pipelines">
              Browse test runs
            </a>
            <button className="ghost-cta" type="button" onClick={() => setViewMode('settings')}>
              Open settings
            </button>
          </div>
        </div>
        <div className="layout__header-actions">
          <div className="pill-toggle" role="tablist" aria-label="Select environment">
            {(['prod', 'staging', 'dev'] satisfies Environment[]).map((envOption) => (
              <button
                key={envOption}
                type="button"
                className={environment === envOption ? 'active' : ''}
                onClick={() => handleEnvironmentChange(envOption)}
                role="tab"
                aria-selected={environment === envOption}
              >
                {envOption.toUpperCase()}
              </button>
            ))}
          </div>
          <div className="pill-toggle" role="tablist" aria-label="Choose dashboard view">
            <button
              type="button"
              className={viewMode === 'summary' ? 'active' : ''}
              onClick={() => setViewMode('summary')}
              role="tab"
              aria-selected={viewMode === 'summary'}
            >
              Summary
            </button>
            <button
              type="button"
              className={viewMode === 'reports' ? 'active' : ''}
              onClick={() => setViewMode('reports')}
              role="tab"
              aria-selected={viewMode === 'reports'}
            >
              Reports
            </button>
            <button
              type="button"
              className={viewMode === 'settings' ? 'active' : ''}
              onClick={() => setViewMode('settings')}
              role="tab"
              aria-selected={viewMode === 'settings'}
            >
              Settings
            </button>
          </div>
        </div>
      </header>

      <main className={`layout__content ${viewMode === 'summary' ? 'layout__content--single' : ''}`}>
        {viewMode === 'summary' ? (
          <section className="content">
            <section className="quick-actions" aria-label="Quick navigation">
              <div className="quick-actions__card">
                <div>
                  <p className="eyebrow">Explore results</p>
                  <h3>Project pipelines</h3>
                  <p className="muted">Search, filter, and jump into the latest runs across every environment.</p>
                </div>
                <a className="inline-link" href="#pipelines">
                  Go to runs
                </a>
              </div>
              <div className="quick-actions__card">
                <div>
                  <p className="eyebrow">Health snapshot</p>
                  <h3>Quality signals</h3>
                  <p className="muted">See passing, failing, and flaky projects at a glance before drilling deeper.</p>
                  <div className="pill-group" role="list" aria-label="Status breakdown">
                    <span className="pill" role="listitem">
                      Passing: {passingCount}
                    </span>
                    <span className="pill pill--amber" role="listitem">
                      Failing: {failingCount}
                    </span>
                    <span className="pill pill--rose" role="listitem">
                      Flaky: {flakyCount}
                    </span>
                  </div>
                </div>
                <a className="inline-link" href="#insights">
                  View insights
                </a>
              </div>
              <div className="quick-actions__card quick-actions__card--accent">
                <div>
                  <p className="eyebrow">Configure access</p>
                  <h3>Project settings</h3>
                  <p className="muted">
                    Register report URLs, choose a default environment, and highlight the teams that own each pipeline.
                  </p>
                </div>
                <button className="ghost-cta" type="button" onClick={() => setViewMode('settings')}>
                  Configure projects
                </button>
              </div>
            </section>
            <div className="panel table-panel" aria-label="Project runs table" id="pipelines">
              <div className="table-panel__header">
                <div>
                  <p className="eyebrow">Runs directory</p>
                  <h3>Project pipelines</h3>
                  <span className="tag">Environment: {environment.toUpperCase()}</span>
                </div>
                <div className="scope-tabs" role="tablist" aria-label="Scope quick filters">
                  {(
                    [
                      { key: 'my-projects', label: 'My Projects' },
                      { key: 'favorites', label: 'Favorites' },
                      { key: 'recent', label: 'Recent' },
                    ] satisfies { key: ScopeFilter; label: string }[]
                  ).map((scope) => (
                    <button
                      key={scope.key}
                      type="button"
                      role="tab"
                      className={scopeFilter === scope.key ? 'active' : ''}
                      aria-selected={scopeFilter === scope.key}
                      onClick={() => setScopeFilter(scope.key)}
                    >
                      {scope.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="table-toolbar" role="region" aria-label="Filter and search projects">
                <label className="table-toolbar__search">
                  <span className="sr-only">Search projects or branches</span>
                  <input
                    type="search"
                    name="search"
                    placeholder="Search projects or branches…"
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                  />
                </label>
                <div className="table-toolbar__filters">
                  <div className="segmented" role="group" aria-label="Status filter">
                    {(
                      [
                        { key: 'all', label: 'All' },
                        { key: 'passing', label: 'Passing' },
                        { key: 'failing', label: 'Failing' },
                        { key: 'flaky', label: 'Flaky' },
                      ] satisfies { key: StatusFilter; label: string }[]
                    ).map((filter) => (
                      <button
                        key={filter.key}
                        type="button"
                        className={statusFilter === filter.key ? 'active' : ''}
                        onClick={() => setStatusFilter(filter.key)}
                        aria-pressed={statusFilter === filter.key}
                      >
                        {filter.label}
                      </button>
                    ))}
                  </div>
                  {hasDates && (
                    <div className="date-range" aria-label="Date range filter">
                      <label>
                        <span className="sr-only">From date</span>
                        <input
                          type="date"
                          value={dateFrom}
                          onChange={(event) => setDateFrom(event.target.value)}
                        />
                      </label>
                      <span className="date-range__separator">to</span>
                      <label>
                        <span className="sr-only">To date</span>
                        <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
                      </label>
                    </div>
                  )}
                </div>
              </div>

              {overviewMessage ? (
                <p className="muted table-panel__message">{overviewMessage}</p>
              ) : (
                <div className="table-container">
                  <table className="overview-table">
                    <thead>
                      <tr>
                        {(
                          [
                            { key: 'project', label: 'Project' },
                            { key: 'branch', label: 'Branch' },
                            { key: 'lastRun', label: 'Last Run' },
                            { key: 'status', label: 'Status' },
                            { key: 'duration', label: 'Duration' },
                          ] satisfies { key: SortKey; label: string }[]
                        ).map((column) => {
                          const isActive = sortState.key === column.key
                          const sortLabel = isActive ? (sortState.direction === 'asc' ? 'ascending' : 'descending') : 'none'
                          return (
                            <th key={column.key} aria-sort={sortLabel as 'none' | 'ascending' | 'descending'}>
                              <button type="button" onClick={() => handleSortChange(column.key)}>
                                <span>{column.label}</span>
                                <span className={`sort-indicator ${isActive ? 'active' : ''}`} aria-hidden="true">
                                  {isActive ? (sortState.direction === 'asc' ? '▲' : '▼') : '↕'}
                                </span>
                              </button>
                            </th>
                          )
                        })}
                        <th aria-hidden="true"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredOverview.length ? (
                        filteredOverview.map((item) => {
                          const detailUrl = `/projects/${encodeURIComponent(item.project)}`
                          const statusLabel =
                            item.derivedStatus === 'passing'
                              ? 'Passing'
                              : item.derivedStatus === 'failing'
                              ? 'Failing'
                              : 'Flaky'

                          return (
                            <tr key={`${item.project}-${item.environment}`}>
                              <td>
                                <div className="table-cell__project">
                                  <button
                                    type="button"
                                    className={`favorite ${favoriteProjects.includes(item.project) ? 'active' : ''}`}
                                    aria-label={favoriteProjects.includes(item.project) ? 'Remove from favorites' : 'Add to favorites'}
                                    onClick={() => toggleFavorite(item.project)}
                                  >
                                    ★
                                  </button>
                                  <div className="table-cell__links">
                                    <a className="primary-link" href={detailUrl}>
                                      {item.project}
                                    </a>
                                    <a className="secondary-link" href={detailUrl} aria-label={`View ${item.project} details`}>
                                      View ↗
                                    </a>
                                  </div>
                                </div>
                              </td>
                              <td>
                                <span className="pill">{item.branchLabel}</span>
                              </td>
                              <td>{formatDateTime(item.lastRun)}</td>
                              <td>
                                <span className={`status status--${item.status}`}>{statusLabel}</span>
                              </td>
                              <td>{formatDuration(item.durationMs)}</td>
                              <td className="table-cell__actions">
                                {item.reportUrl && (
                                  <a className="inline-link" href={item.reportUrl} target="_blank" rel="noreferrer">
                                    Open report
                                  </a>
                                )}
                              </td>
                            </tr>
                          )
                        })
                      ) : (
                        <tr>
                          <td colSpan={6} className="table-empty">
                            No projects match your filters.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}
              <div aria-live="polite" className="sr-only">
                {sortAnnouncement}
              </div>
            </div>

            <div id="insights">
              <SummaryGrid overview={overview} statusMessage={overviewMessage} environment={environment} />
            </div>
            <ProjectTable
              overview={overview}
              statusMessage={overviewMessage}
              environment={environment}
            />
          </section>
        ) : viewMode === 'reports' ? (
          <>
            <aside className="panel">
              <ProjectList
                projects={projects}
                selected={selectedProject?.project ?? ''}
                onSelect={handleSelect}
                statusMessage={statusMessage}
                environment={environment}
              />
            </aside>
            <section className="content">
              {selectedProject && selectedProject.reportUrl ? (
                <ReportFrame
                  project={selectedProject.project}
                  url={selectedProject.reportUrl}
                  environment={selectedProject.environment}
                />
              ) : (
                <div className="empty-state">
                  <h3>Select a project to view its latest Allure report</h3>
                  <p>Upload reports via the API to start browsing results.</p>
                </div>
              )}
            </section>
          </>
        ) : (
          <section className="content settings" aria-label="Project configuration" id="settings">
            <div className="panel settings__intro">
              <p className="eyebrow">Configuration</p>
              <h3>Project settings</h3>
              <p className="muted">
                Define how teams access their Allure reports, pick a default environment for the dashboard, and keep
                metadata handy when triaging issues.
              </p>
              <div className="settings__tips">
                <div>
                  <strong>Tip:</strong> Use a short project name so it lines up with pipeline labels and table filters.
                </div>
                <div>
                  <strong>Need to add owners?</strong> Fill in the description with team details and service links.
                </div>
              </div>
            </div>

            <div className="settings__grid">
              <form className="panel settings__form" onSubmit={handleConfigSubmit}>
                <div>
                  <p className="eyebrow">Add configuration</p>
                  <h4>Register a project</h4>
                  <p className="muted">
                    Capture the essentials for each test project so anyone landing on the dashboard can open the right
                    report.
                  </p>
                </div>

                <label>
                  <span>Project name</span>
                  <input
                    required
                    value={configForm.name}
                    onChange={(event) => setConfigForm({ ...configForm, name: event.target.value })}
                    placeholder="e.g. Checkout service"
                  />
                </label>

                <label>
                  <span>Report URL</span>
                  <input
                    required
                    type="url"
                    value={configForm.reportUrl}
                    onChange={(event) => setConfigForm({ ...configForm, reportUrl: event.target.value })}
                    placeholder="https://reports.example.com/checkout"
                  />
                </label>

                <label>
                  <span>Environment</span>
                  <select
                    value={configForm.environment}
                    onChange={(event) => setConfigForm({ ...configForm, environment: event.target.value as Environment })}
                  >
                    {(['prod', 'staging', 'dev'] satisfies Environment[]).map((envOption) => (
                      <option value={envOption} key={envOption}>
                        {envOption.toUpperCase()}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  <span>Notes</span>
                  <textarea
                    value={configForm.description}
                    onChange={(event) => setConfigForm({ ...configForm, description: event.target.value })}
                    placeholder="Team name, service links, alert channel, or triage steps"
                  />
                </label>

                <button type="submit" className="primary-cta">
                  Save configuration
                </button>
              </form>

              <div className="panel settings__list">
                <div className="settings__list-header">
                  <div>
                    <p className="eyebrow">Default preferences</p>
                    <h4>Environment and projects</h4>
                    <p className="muted">
                      Pick where the dashboard should start, then review the projects that have been registered so far.
                    </p>
                  </div>
                  <div className="segmented" role="group" aria-label="Default environment">
                    {(['prod', 'staging', 'dev'] satisfies Environment[]).map((envOption) => (
                      <button
                        type="button"
                        key={envOption}
                        className={environment === envOption ? 'active' : ''}
                        onClick={() => handleEnvironmentChange(envOption)}
                        aria-pressed={environment === envOption}
                      >
                        {envOption.toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>

                {projectConfigs.length ? (
                  <ul className="settings__items" aria-label="Configured projects">
                    {projectConfigs.map((config) => (
                      <li key={config.name} className="settings__item">
                        <div>
                          <div className="settings__item-heading">
                            <h5>{config.name}</h5>
                            <span className="pill">{config.environment.toUpperCase()}</span>
                          </div>
                          <p className="muted">{config.description || 'No notes added yet.'}</p>
                          <a className="inline-link" href={config.reportUrl} target="_blank" rel="noreferrer">
                            Open report
                          </a>
                        </div>
                        <button type="button" className="ghost-cta" onClick={() => handleConfigDelete(config.name)}>
                          Remove
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="empty-state">
                    <h4>No projects configured yet</h4>
                    <p>Add a few key projects to make onboarding easier for the rest of the team.</p>
                  </div>
                )}
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
