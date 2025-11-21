import { useEffect, useMemo, useState } from 'react'
import { fetchProjectOverview, fetchProjects } from './api'
import { ProjectList } from './components/ProjectList'
import { ReportFrame } from './components/ReportFrame'
import { SummaryGrid } from './components/SummaryGrid'
import type { ProjectOverview, ProjectSummary } from './types'
import './styles/layout.css'

function App() {
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [overview, setOverview] = useState<ProjectOverview[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [overviewLoading, setOverviewLoading] = useState(true)
  const [overviewError, setOverviewError] = useState<string | null>(null)
  const [selectedProject, setSelectedProject] = useState<ProjectSummary | null>(null)
  const [viewMode, setViewMode] = useState<'summary' | 'reports'>('summary')

  useEffect(() => {
    fetchProjects()
      .then((data) => {
        setProjects(data)
        setSelectedProject((current) => current ?? data[0] ?? null)
      })
      .catch(() => setError('Unable to load projects. Please check the API service.'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    fetchProjectOverview()
      .then((data) => setOverview(data))
      .catch(() => setOverviewError('Unable to load project overview. Please check the API service.'))
      .finally(() => setOverviewLoading(false))
  }, [])

  const handleSelect = (projectName: string) => {
    const target = projects.find((project) => project.project === projectName)
    if (target) setSelectedProject(target)
  }

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

  return (
    <div className="layout">
      <header className="layout__header">
        <div>
          <p className="eyebrow">QA / Test Engineering</p>
          <h1>Test Results Dashboard</h1>
          <p className="subtitle">Upload and browse Allure reports per project.</p>
        </div>
        <div className="layout__header-actions">
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
          </div>
        </div>
      </header>

      <main className={`layout__content ${viewMode === 'summary' ? 'layout__content--single' : ''}`}>
        {viewMode === 'summary' ? (
          <section className="content">
            <SummaryGrid overview={overview} statusMessage={overviewMessage} />
          </section>
        ) : (
          <>
            <aside className="panel">
              <ProjectList
                projects={projects}
                selected={selectedProject?.project ?? ''}
                onSelect={handleSelect}
                statusMessage={statusMessage}
              />
            </aside>
            <section className="content">
              {selectedProject && selectedProject.reportUrl ? (
                <ReportFrame project={selectedProject.project} url={selectedProject.reportUrl} />
              ) : (
                <div className="empty-state">
                  <h3>Select a project to view its latest Allure report</h3>
                  <p>Upload reports via the API to start browsing results.</p>
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  )
}

export default App
