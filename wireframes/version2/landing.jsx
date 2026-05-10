// Landing screen — editorial hero entry point that funnels into the workspace.
const Landing = ({ onEnter }) => {
  const photos = window.ABF_PHOTOS;
  return (
    <div className="landing">
      <header className="topbar" style={{ position: 'absolute', top: 0, left: 0, right: 0, zIndex: 10, background: 'transparent', borderBottom: 0, color: '#fff' }}>
        <div className="brand" style={{ borderRight: '1px solid rgba(255,255,255,0.18)' }}>
          <div className="brand-mark" style={{ background: '#fff', color: 'var(--text)' }}>af</div>
          <div className="brand-text">
            <div className="brand-name" style={{ color: '#fff' }}>Austin Build Feasibility</div>
            <div className="brand-sub" style={{ color: 'rgba(255,255,255,0.7)' }}>advisory feasibility · stage 0</div>
          </div>
        </div>
        <div className="project-meta" style={{ color: 'rgba(255,255,255,0.7)' }}>
          <span>Workspace</span><span className="dot" style={{ background: 'rgba(255,255,255,0.4)' }}/>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>v0.7.4</span>
        </div>
        <span className="advisory-badge" style={{ background: 'rgba(255,255,255,0.12)', borderColor: 'rgba(255,255,255,0.3)', color: '#fff' }}><span className="pulse"/>Advisory feasibility · not City approval</span>
        <div className="topbar-spacer"/>
        <div className="topbar-actions">
          <button className="hero-btn ghost" style={{ height: 34, padding: '0 14px', fontSize: 12.5 }} onClick={onEnter}>Open workspace<Icon name="arrow-right" size={13}/></button>
        </div>
      </header>

      <section className="hero">
        <div className="hero-img" style={{ backgroundImage: `url(${photos.hero})` }} />
        <div className="hero-content">
          <div className="hero-eyebrow"><span className="line"/>Austin · advisory feasibility for residential infill</div>
          <h1 className="hero-h1">A quiet workspace for <em>infill</em> feasibility in Austin.</h1>
          <p className="hero-sub">Capture build specs, surface candidate lots, screen advisory zoning and environmental signals, draft one schematic plan, and assemble a packet your architect, civil engineer, surveyor, and attorney can actually use.</p>
          <div className="hero-actions">
            <button className="hero-btn primary" onClick={onEnter}>Start a feasibility run<Icon name="arrow-right" size={14}/></button>
            <button className="hero-btn ghost" onClick={onEnter}>Resume project · PRJ-0247</button>
          </div>
        </div>
      </section>

      <section className="landing-section">
        <div className="landing-eyebrow">The workflow</div>
        <h2 className="landing-h2">Six steps from a back-of-the-napkin spec to a reviewer-ready packet.</h2>
        <p className="landing-lead">Each stage produces a structured artifact you can hand to a licensed professional. None of it is City of Austin approval — it's the operational scaffolding around their work.</p>
        <div className="workflow-grid">
          {[
            { num: '01', title: 'Project intake', desc: 'Structured spec plus a conversational request, normalized to a validated contract with assumptions and warnings made explicit.', meta: 'Output · Validated spec' },
            { num: '02', title: 'Lot discovery', desc: 'Ranked prototype candidates from the static dataset with reasoning. Cross-reference against TCAD before action.', meta: 'Output · Ranked candidates' },
            { num: '03', title: 'Lot context', desc: 'Selected parcel detail, source metadata, aerial reference, and explicit pending official joins.', meta: 'Output · Lot context dossier' },
            { num: '04', title: 'Compliance', desc: 'Advisory metrics across zoning, setbacks, coverage, environment, permitting, and safety — every row labelled with confidence and basis.', meta: 'Output · Compliance matrix' },
            { num: '05', title: 'Primary schematic', desc: 'One conceptual plan with room schedule and a deterministic quality checker. Conceptual only — not permit-ready architecture.', meta: 'Output · Schematic SVG' },
            { num: '06', title: 'Review packet', desc: 'Per-reviewer checklists with document slots for architect, civil engineer, surveyor, attorney, and city official.', meta: 'Output · Reviewer bundle' },
          ].map(s => (
            <div key={s.num} className="workflow-card">
              <div className="num">{s.num}</div>
              <div className="title">{s.title}</div>
              <div className="desc">{s.desc}</div>
              <div className="meta">{s.meta}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="landing-section compact">
        <div className="intake-launch">
          <div className="intake-launch-left">
            <div>
              <div className="landing-eyebrow">Begin a project</div>
              <h2 className="landing-h2" style={{ fontSize: 38 }}>Open the workspace and capture a build spec.</h2>
              <p style={{ color: 'var(--text-2)', fontSize: 15, lineHeight: 1.55, maxWidth: '46ch' }}>
                Each project carries a persistent advisory disclaimer, a validated contract, and an audit log of assumptions. Static dataset rows are labelled prominently — never confused with current inventory.
              </p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <button className="hero-btn primary" style={{ background: 'var(--text)', color: '#fff', borderColor: 'var(--text)' }} onClick={onEnter}>Open workspace<Icon name="arrow-right" size={14}/></button>
                <button className="hero-btn ghost" style={{ borderColor: 'var(--border-strong)', color: 'var(--text)' }} onClick={onEnter}>Continue PRJ-0247</button>
              </div>
              <div style={{ display: 'flex', gap: 18, color: 'var(--text-3)', fontSize: 12, fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                <span>Owner · M. Ramirez</span><span>·</span>
                <span>Updated · today</span><span>·</span>
                <span>Mode · advisory</span>
              </div>
            </div>
          </div>
          <div className="intake-launch-img" style={{ backgroundImage: `url(${photos.workspace})` }} />
        </div>
      </section>

      <section className="testimonial">
        <div className="testimonial-inner">
          <div className="testimonial-quote">
            "The point isn't to replace our architect. It's to walk in with a packet that respects her time — assumptions, sources, and known unknowns already on the page."
          </div>
          <div className="testimonial-attrib">M. Ramirez · principal · Ramirez & Co. infill development</div>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="brand-mark" style={{ width: 24, height: 24, fontSize: 13 }}>af</div>
        <div style={{ fontFamily: 'var(--font-serif)', fontSize: 16, color: 'var(--text)' }}>Austin Build Feasibility</div>
        <span style={{ flex: 1 }}/>
        <span>Advisory feasibility only — not a substitute for licensed professional review.</span>
        <span className="dot" style={{ background: 'var(--text-4)' }}/>
        <span style={{ fontFamily: 'var(--font-mono)' }}>v0.7.4 · stage 0</span>
      </footer>
    </div>
  );
};
window.Landing = Landing;
