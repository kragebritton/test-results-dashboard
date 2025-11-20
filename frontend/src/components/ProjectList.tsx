import type { ProjectSummary } from '../App'
import './ProjectList.css'

type Props = {
  projects: ProjectSummary[]
  selected: string
  statusMessage: string | null
  onSelect: (project: string) => void
}

export function ProjectList({ projects, selected, statusMessage, onSelect }: Props) {
  if (statusMessage) {
    return (
      <div className="project-list project-list--empty">
        <p>{statusMessage}</p>
      </div>
    )
  }

  return (
    <div className="project-list">
      <div className="project-list__header">
        <h3>Projects</h3>
        <p className="muted">Latest Allure report per project</p>
      </div>
      <ul>
        {projects.map((project) => (
          <li key={project.project} className={selected === project.project ? 'active' : ''}>
            <button type="button" onClick={() => onSelect(project.project)}>
              <span className="name">{project.project}</span>
              {project.latest && (
                <span className="badge" title={`Latest build: ${project.latest}`}>
                  {project.latest}
                </span>
              )}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
