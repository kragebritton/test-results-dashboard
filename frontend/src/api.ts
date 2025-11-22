import { ProjectOverview, ProjectSummary } from './types'

export async function fetchProjects(environment: string): Promise<ProjectSummary[]> {
  const response = await fetch(`/api/projects?environment=${encodeURIComponent(environment)}`)
  if (!response.ok) {
    throw new Error('Failed to fetch projects')
  }
  return response.json()
}

export async function fetchProjectOverview(environment: string): Promise<ProjectOverview[]> {
  const response = await fetch(`/api/overview?environment=${encodeURIComponent(environment)}`)
  if (!response.ok) {
    throw new Error('Failed to fetch overview')
  }
  return response.json()
}
