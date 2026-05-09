import { IntakeForm } from "@/components/intake/intake-form";

const workflow = [
  "Intake",
  "Lot discovery",
  "Parcel context",
  "Compliance",
  "Schematic design",
  "Visuals",
  "Review packet"
];

export default function HomePage() {
  return (
    <main className="shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Stage 0 foundation</p>
          <h1>Austin Build Feasibility AI</h1>
          <p className="lede">
            A staged platform for Austin lot search, zoning-aware feasibility, schematic concepts,
            AI visuals, and professional review packets.
          </p>
        </div>
      </section>

      <IntakeForm />

      <section className="panel">
        <h2>Workflow</h2>
        <ol className="workflow">
          {workflow.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
      </section>

      <section className="notice">
        This is advisory feasibility support, not official city approval or professional advice.
      </section>
    </main>
  );
}
