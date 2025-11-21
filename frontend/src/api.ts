import { ProjectOverview, ProjectSummary } from './types'

export async function fetchProjects(): Promise<ProjectSummary[]> {
  const response = await fetch('/api/projects')
  if (!response.ok) {
    throw new Error('Failed to fetch projects')
  }
  return response.json()
}

export async function fetchProjectOverview(): Promise<ProjectOverview[]> {
  const response = await fetch('/api/overview')
  if (!response.ok) {
    throw new Error('Failed to fetch overview')
  }
  return response.json()
}
