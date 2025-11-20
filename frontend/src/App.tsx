import { useEffect, useMemo, useState } from 'react'
import { fetchProjects } from './api'
import { ProjectList } from './components/ProjectList'
import { ReportFrame } from './components/ReportFrame'
import './styles/layout.css'

export type ProjectSummary = {
  project: string
  latest: string | null
  history: { build_id: string; uploaded_at: string }[]
  reportUrl: string | null
}

function App() {
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedProject, setSelectedProject] = useState<ProjectSummary | null>(null)

  useEffect(() => {
    fetchProjects()
      .then((data) => {
        setProjects(data)
        setSelectedProject((current) => current ?? data[0] ?? null)
      })
      .catch(() => setError('Unable to load projects. Please check the API service.'))
      .finally(() => setLoading(false))
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

  return (
    <div className="layout">
      <header className="layout__header">
        <div>
          <p className="eyebrow">QA / Test Engineering</p>
          <h1>Test Results Dashboard</h1>
          <p className="subtitle">Upload and browse Allure reports per project.</p>
        </div>
      </header>

      <main className="layout__content">
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
      </main>
    </div>
  )
}

export default App
