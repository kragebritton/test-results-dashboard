import './ReportFrame.css'

type Props = {
  project: string
  url: string
}

export function ReportFrame({ project, url }: Props) {
  return (
    <div className="report-frame">
      <div className="report-frame__header">
        <div>
          <p className="eyebrow">Project</p>
          <h2>{project}</h2>
        </div>
        <a className="external-link" href={url} target="_blank" rel="noreferrer">
          Open report in new tab
        </a>
      </div>
      <iframe src={url} title={`${project} Allure report`} />
    </div>
  )
}
