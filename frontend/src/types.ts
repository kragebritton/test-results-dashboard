export type HistoryEntry = { build_id: string; uploaded_at: string }

export type ProjectSummary = {
  project: string
  latest: string | null
  history: HistoryEntry[]
  reportUrl: string | null
}

export type ProjectOverview = {
  project: string
  latest: string | null
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
