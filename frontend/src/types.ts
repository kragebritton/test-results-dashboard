export type Environment = 'dev' | 'staging' | 'prod'

export type HistoryEntry = { build_id: string; uploaded_at: string; environment: Environment }

export type ProjectSummary = {
  project: string
  latest: string | null
  history: HistoryEntry[]
  environment: Environment
  reportUrl: string | null
}

export type ProjectOverview = {
  project: string
  latest: string | null
  environment: Environment
  lastRun: string | null
  status: 'passed' | 'failed' | 'unknown'
  statistics: {
    passed: number
    failed: number
    broken: number
    skipped: number
    unknown: number
    total: number
  }
  reportUrl: string | null
}
