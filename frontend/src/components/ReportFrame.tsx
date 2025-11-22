import type { Environment } from '../types'
import './ReportFrame.css'

type Props = {
  project: string
  url: string
  environment: Environment
}

export function ReportFrame({ project, url, environment }: Props) {
  return (
    <div className="report-frame">
      <div className="report-frame__header">
        <div>
          <p className="eyebrow">Project</p>
          <h2>{project}</h2>
          <span className="tag">Environment: {environment.toUpperCase()}</span>
        </div>
        <a className="external-link" href={url} target="_blank" rel="noreferrer">
          Open report in new tab
        </a>
      </div>
      <iframe src={url} title={`${project} Allure report`} />
    </div>
  )
}
