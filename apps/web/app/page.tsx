import { IntakeForm } from "@/components/intake/intake-form";

const workflow = [
  "Stage 0 · Contracts",
  "Stage 1 · Intake",
  "Stage 2 · Public data",
  "Stage 3 · Lot ranking",
  "Stage 4 · Parcel context",
  "Stage 5 · Feasibility",
  "Stage 6 · Schematics paused"
];

const publicDataSources = [
  {
    label: "Austin permits",
    detail: "Socrata 3syk-w9eu",
    endpoint: "/data/austin/permits/recent"
  },
  {
    label: "Zoning layer",
    detail: "ArcGIS Publish_Zoning_AGOL",
    endpoint: "/data/austin/zoning/sample"
  },
  {
    label: "TCAD parcels",
    detail: "ArcGIS EXTERNAL_tcad_parcel",
    endpoint: "/data/austin/parcels/sample"
  }
];

export default function HomePage() {
  return (
    <div className="app-frame">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">af</div>
          <div className="brand-text">
            <strong>Austin Build Feasibility</strong>
            <span>stage 2 · public data wireframe</span>
          </div>
        </div>
        <div className="project-meta">
          <span>Austin ADU feasibility</span>
          <span className="dot" />
          <span>prototype static dataset</span>
        </div>
        <span className="advisory-badge">Advisory · not City approval</span>
      </header>

      <div className="app-body">
        <aside className="rail" aria-label="Workflow">
          <div className="rail-header">Workflow</div>
          <ol className="rail-list">
            {workflow.map((item, index) => (
              <li className={index === 2 ? "active" : index < 2 ? "complete" : ""} key={item}>
                <span>{index < 2 ? "✓" : index + 1}</span>
                <strong>{item}</strong>
              </li>
            ))}
          </ol>
          <div className="rail-foot">
            <span>Mode</span>
            <strong>advisory</strong>
          </div>
        </aside>

        <main className="work">
          <section className="work-header">
            <div>
              <p className="eyebrow">Stage 2 wireframe</p>
              <h1>Austin Build Feasibility AI</h1>
              <p className="lede">
                Operational workspace for Austin public-data ingestion, lot screening,
                feasibility context, and review-ready project records.
              </p>
            </div>
            <div className="status-card">
              <strong>Current focus</strong>
              <span>Public data + intake workflow</span>
            </div>
          </section>

          <section className="source-strip" aria-label="Stage 2 public data sources">
            {publicDataSources.map((source) => (
              <article className="source-card" key={source.endpoint}>
                <strong>{source.label}</strong>
                <span>{source.detail}</span>
                <code>{source.endpoint}</code>
              </article>
            ))}
          </section>

          <IntakeForm />

          <section className="notice">
            This is advisory feasibility support, not official city approval or professional advice.
          </section>
        </main>
      </div>
    </div>
  );
}
