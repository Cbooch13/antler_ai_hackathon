import { Icon } from '../components/Icon';
import { Btn, Status, Banner, LockedState } from '../components';
import { JsonView } from '../components/JsonView';
import { fmt } from '../components';
import { lots, compliance, schematic, packet, validatedContract, project } from '../data/mock';
import { STEPS } from '../App';
import type { WorkflowState, RunStates, JobName } from '../types';

const STATUS_BADGE: Record<string, { kind: 'passes' | 'warning' | 'fail' | 'unknown' | 'info'; label: string }> = {
  'ready':       { kind: 'passes',  label: 'Ready' },
  'in-review':   { kind: 'info',    label: 'In review' },
  'blocked':     { kind: 'fail',    label: 'Blocked' },
  'not-started': { kind: 'unknown', label: 'Not started' },
  'draft':       { kind: 'warning', label: 'Draft' },
  'missing':     { kind: 'unknown', label: 'Missing' },
};

const ROLE_SUB: Record<string, string> = {
  'Architect':     'Design intent & code-rated separation',
  'Civil Engineer': 'Drainage, impervious, site work',
  'Surveyor':      'Boundary, topo, tree survey',
  'Attorney':      'Title, deed, covenant review',
  'City Official': 'Pre-application & overlay checks',
};

interface MobilePreviewProps {
  state: WorkflowState;
  setState: React.Dispatch<React.SetStateAction<WorkflowState>>;
  run: (job: JobName) => void;
  onClose: () => void;
}

export function MobilePreview({ state, setState, run, onClose }: MobilePreviewProps) {
  const screen = state.screen;
  return (
    <div className="m-screen">
      <div className="m-topbar">
        <div className="m-row1">
          <button className="btn btn-sm btn-ghost btn-icon" onClick={onClose} aria-label="Close mobile preview">
            <Icon name="back" size={14} />
          </button>
          <div style={{ minWidth: 0 }}>
            <div className="m-title">Austin Build Feasibility AI</div>
            <div style={{ fontSize: 10.5, color: 'var(--text-3)', fontFamily: 'var(--font-mono)' }}>{project.name}</div>
          </div>
          <span style={{ flex: 1 }} />
          <span className="advisory-badge"><span className="pulse" />Advisory</span>
        </div>
      </div>

      <div className="m-stepper">
        {STEPS.map((s, i) => {
          const status = i + 1 < state.step ? 'complete' : (state.screen === s.key ? 'active' : (i + 1 > state.step ? 'locked' : ''));
          return (
            <button
              key={s.key}
              className={'m-step ' + status}
              onClick={() => i + 1 <= state.step && setState(st => ({ ...st, screen: s.key }))}
            >
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}>{i + 1}</span>
              <span>{s.short}</span>
              {status === 'complete' && <Icon name="check" size={11} />}
              {status === 'locked' && <Icon name="lock" size={10} />}
            </button>
          );
        })}
      </div>

      <div className="m-content">
        {screen === 'intake'      && <MobileIntake state={state} setState={setState} run={run} />}
        {screen === 'lots'        && <MobileLots state={state} setState={setState} />}
        {screen === 'lot-context' && <MobileLotContext state={state} run={run} runStates={{}} />}
        {screen === 'compliance'  && <MobileCompliance run={run} runStates={{}} />}
        {screen === 'schematic'   && <MobileSchematic setState={setState} />}
        {screen === 'packet'      && <MobilePacket />}
      </div>

      <div className="m-disclaimer">
        <span className="d" style={{ width: 5, height: 5, background: 'var(--warn)', borderRadius: '50%' }} />
        Advisory feasibility — not official Austin approval.
      </div>
    </div>
  );
}

function MobileIntake({ state, setState, run }: { state: WorkflowState; setState: MobilePreviewProps['setState']; run: MobilePreviewProps['run'] }) {
  const i = state.intake;
  const update = (k: keyof typeof i, v: unknown) => setState(s => ({ ...s, intake: { ...s.intake, [k]: v } }));
  return (
    <>
      <div className="m-card">
        <div className="m-card-h">
          <strong>Project intake</strong>
          <Status kind={state.validated ? 'passes' : 'unknown'} label={state.validated ? 'Validated' : 'Pending'} />
        </div>
        <div className="m-card-b" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div className="field"><label className="label">Project name</label><input className="input" value={i.projectName} onChange={e => update('projectName', e.target.value)} /></div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div className="field"><label className="label">Type</label><select className="select" value={i.propertyType} onChange={e => update('propertyType', e.target.value)}><option>ADU</option><option>Single-family</option><option>Duplex</option></select></div>
            <div className="field"><label className="label">Risk</label><select className="select" value={i.riskTolerance} onChange={e => update('riskTolerance', e.target.value)}><option>Low</option><option>Medium</option><option>High</option></select></div>
            <div className="field"><label className="label">Budget</label><input className="input mono" type="number" value={i.budget} onChange={e => update('budget', +e.target.value)} /></div>
            <div className="field"><label className="label">Units</label><input className="input mono" type="number" value={i.units} onChange={e => update('units', +e.target.value)} /></div>
            <div className="field"><label className="label">Lot sqft</label><input className="input mono" type="number" value={i.lotSqft} onChange={e => update('lotSqft', +e.target.value)} /></div>
            <div className="field"><label className="label">Bldg sqft</label><input className="input mono" type="number" value={i.buildingSqft} onChange={e => update('buildingSqft', +e.target.value)} /></div>
            <div className="field"><label className="label">Beds</label><input className="input mono" type="number" value={i.beds} onChange={e => update('beds', +e.target.value)} /></div>
            <div className="field"><label className="label">Baths</label><input className="input mono" type="number" value={i.baths} onChange={e => update('baths', +e.target.value)} /></div>
          </div>
          <Btn size="sm" onClick={() => run('validate')}>Validate spec</Btn>
        </div>
      </div>

      <div className="m-card">
        <div className="m-card-h"><strong>Conversational request</strong></div>
        <div className="m-card-b" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <textarea className="textarea" rows={3} value={state.conversation} onChange={e => setState(s => ({ ...s, conversation: e.target.value }))} />
          <Btn size="sm" icon="refresh" onClick={() => run('normalize')}>Normalize</Btn>
        </div>
      </div>

      <div className="m-card">
        <div className="m-card-h"><strong>Validated contract</strong><span className="kbd">JSON</span></div>
        <div className="m-card-b" style={{ padding: 0 }}>
          <JsonView data={validatedContract.spec} />
        </div>
      </div>

      <Btn size="lg" variant="primary" iconRight="arrow-right" disabled={!state.validated} onClick={() => run('findLots')}>
        Find prototype lots
      </Btn>
    </>
  );
}

function MobileLots({ state, setState }: { state: WorkflowState; setState: MobilePreviewProps['setState'] }) {
  return (
    <>
      <Banner kind="warning" title="Prototype/static dataset — not current inventory">
        Cross-reference parcel identity with TCAD before any decisions.
      </Banner>
      <div style={{ marginLeft: -12, marginRight: -12, marginTop: 4 }}>
        <div className="m-swipe-row">
          {lots.map((l, i) => {
            const sel = state.selectedLotId === l.id;
            return (
              <div
                key={l.id}
                className="m-lot-card"
                onClick={() => setState(s => ({ ...s, selectedLotId: l.id, step: Math.max(s.step, 2) }))}
                style={{ borderColor: sel ? 'var(--teal)' : undefined, boxShadow: sel ? '0 0 0 1px var(--teal) inset' : undefined }}
              >
                <div className="m-lot-body" style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-3)', fontSize: 10 }}>RANK #{i + 1}</span>
                    <span style={{ flex: 1 }} />
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{l.score.toFixed(l.score === 100 ? 0 : 1)}/100</span>
                  </div>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{l.address}</div>
                  <div style={{ color: 'var(--text-3)', fontSize: 11 }}>{l.neighborhood}</div>
                  <div style={{ display: 'flex', gap: 10, fontSize: 11, color: 'var(--text-2)', flexWrap: 'wrap' }}>
                    <span><span className="mono">{fmt.money(l.price)}</span></span>
                    <span>·</span>
                    <span><span className="mono">{fmt.num(l.lotSqft)}</span> sqft</span>
                    <span>·</span>
                    <span>{l.units} unit</span>
                  </div>
                  <span className="lot-prototype-tag" style={{ alignSelf: 'flex-start', marginTop: 4 }}>prototype/static</span>
                  <Btn size="sm" iconRight="chevron-r" style={{ marginTop: 6 }} onClick={(e) => { e.stopPropagation(); setState(s => ({ ...s, selectedLotId: l.id, screen: 'lot-context', step: Math.max(s.step, 3) })); }}>View context</Btn>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}

function MobileLotContext({ state, run, runStates }: { state: WorkflowState; run: MobilePreviewProps['run']; runStates: RunStates }) {
  const lot = lots.find(l => l.id === state.selectedLotId);
  if (!lot) return <LockedState title="No lot selected" body="Pick a lot first." />;
  return (
    <>
      <div className="m-card">
        <div className="m-card-h"><strong>{lot.address}</strong><span className="lot-prototype-tag">prototype</span></div>
        <div className="map-placeholder" style={{ height: 180, borderRadius: 0, borderLeft: 0, borderRight: 0, borderTop: 0, borderBottom: '1px solid var(--border)' }}>
          <div className="map-overlay">{lot.coords.lat.toFixed(3)}, {lot.coords.lng.toFixed(3)}</div>
          <div className="map-pin" />
          <div className="map-attribution">map placeholder</div>
        </div>
        <div className="m-card-b">
          <div className="kvs">
            <div className="k">Neighborhood</div><div className="v">{lot.neighborhood}</div>
            <div className="k">Lot</div><div className="v">{fmt.num(lot.lotSqft)} sqft</div>
            <div className="k">Price</div><div className="v">{fmt.money(lot.price)}</div>
            <div className="k">Beds/Baths</div><div className="v">{lot.beds}/{lot.baths}</div>
            <div className="k">Units</div><div className="v">{lot.units}</div>
            <div className="k">Parcel id</div><div className="v"><span className="muted">pending</span></div>
            <div className="k">Zoning</div><div className="v"><span className="muted">pending</span></div>
          </div>
        </div>
      </div>
      <Banner kind="warning" title="Official parcel/zoning joins pending">TCAD lookup required before design decisions.</Banner>
      <Btn size="lg" variant="primary" loading={runStates.feasibility === 'loading'} iconRight="arrow-right" onClick={() => run('feasibility')}>
        Run feasibility check
      </Btn>
    </>
  );
}

function FindingColMobile({ kind, title, items }: { kind: string; title: string; items: Array<{ title: string; body: string }> }) {
  return (
    <div className="finding-col">
      <div className="finding-col-h">
        <span className="t">{title}</span>
        <Status kind={kind as 'passes' | 'warning' | 'fail' | 'unknown' | 'info'} label={String(items.length)} />
      </div>
      {items.length === 0
        ? <div style={{ padding: 10, textAlign: 'center', color: 'var(--text-3)', fontSize: 11 }}>none</div>
        : items.slice(0, 2).map((f, i) => <div key={i} className="finding"><div className="finding-t">{f.title}</div></div>)}
    </div>
  );
}

function MobileCompliance({ run, runStates }: { run: MobilePreviewProps['run']; runStates: RunStates }) {
  const c = compliance;
  return (
    <>
      <Banner kind="warning" title={`${c.findings} advisory findings`}>{c.needsReview} require review or additional data.</Banner>
      <div className="m-tbl-wrap">
        <table className="tbl">
          <thead><tr><th>Category</th><th>Metric</th><th>Value</th><th>Status</th><th>Conf.</th><th>Notes</th></tr></thead>
          <tbody>
            {c.rows.map((r, i) => (
              <tr key={i}>
                <td className="text-2">{r.category}</td>
                <td style={{ fontWeight: 500 }}>{r.metric}</td>
                <td className="measure">{r.value}</td>
                <td><Status kind={r.status} /></td>
                <td><span className="badge neutral"><span className="d" />{r.confidence}</span></td>
                <td className="text-2">{r.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="finding-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
        <FindingColMobile kind="passes"  title="Passes"   items={c.findingsGrouped.passes} />
        <FindingColMobile kind="warning" title="Warnings" items={c.findingsGrouped.warnings} />
        <FindingColMobile kind="unknown" title="Unknowns" items={c.findingsGrouped.unknowns} />
        <FindingColMobile kind="fail"    title="Fails"    items={c.findingsGrouped.fails} />
      </div>
      <Btn size="lg" variant="primary" loading={runStates.plan === 'loading'} iconRight="arrow-right" onClick={() => run('plan')}>
        Generate schematic plan
      </Btn>
    </>
  );
}

function MobileSchematic({ setState }: { setState: MobilePreviewProps['setState'] }) {
  const s = schematic;
  return (
    <>
      <div className="m-card">
        <div className="m-card-h"><strong>{s.name}</strong><Status kind="fail" label={`Q ${s.qualityScore}/100`} /></div>
        <div className="m-card-b">
          <div className="plan-stats" style={{ gridTemplateColumns: '1fr 1fr' }}>
            <div className="plan-stat"><div className="plan-stat-l">Target</div><div className="plan-stat-v">{fmt.num(s.targetSqft)} sqft</div></div>
            <div className="plan-stat" style={{ borderRight: 0 }}><div className="plan-stat-l">Units</div><div className="plan-stat-v">{s.units}</div></div>
          </div>
        </div>
      </div>
      <div className="m-card">
        <div className="m-card-h"><strong>Room schedule</strong><span className="kbd">{s.rooms.length} rooms</span></div>
        <div className="m-tbl-wrap" style={{ border: 0, borderRadius: 0 }}>
          <table className="tbl">
            <thead><tr><th>Room</th><th>Sqft</th><th>Dim</th><th>L</th></tr></thead>
            <tbody>
              {s.rooms.map((r, i) => (
                <tr key={i}><td style={{ fontWeight: 500 }}>{r.name}</td><td className="measure">{r.sqft}</td><td className="measure">{r.dim}</td><td className="measure">{r.level}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="m-card">
        <div className="m-card-h"><strong>Quality checks</strong></div>
        <div className="qc-list">
          {s.qualityChecks.map((q, i) => (
            <div key={i} className={'qc-row' + (q.status === 'fail' ? ' fail' : '')}>
              <div className={'qc-mark ' + q.status}>{q.status === 'pass' ? '✓' : '!'}</div>
              <div><div className="qc-name">{q.name}</div><div className="qc-body">{q.body}</div></div>
              <div />
            </div>
          ))}
        </div>
      </div>
      <Btn size="lg" variant="primary" iconRight="arrow-right" onClick={() => setState(st => ({ ...st, screen: 'packet', step: Math.max(st.step, 6) }))}>
        Assemble review packet
      </Btn>
    </>
  );
}

function MobilePacket() {
  return (
    <>
      <Banner kind="warning" title="Not official approval">Bundles advisory feasibility evidence for licensed reviewers.</Banner>
      {packet.groups.map(g => {
        const sb = STATUS_BADGE[g.status] ?? { kind: 'unknown' as const, label: g.status };
        const missing = g.documents.filter(d => d.required && d.status === 'missing').length;
        return (
          <div key={g.role} className="m-card">
            <div className="m-card-h"><strong>{g.role}</strong><Status kind={sb.kind} label={sb.label} /></div>
            <div className="m-card-b">
              <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 6 }}>{ROLE_SUB[g.role]}</div>
              <div className="doc-list">
                {g.documents.map((d, i) => {
                  const dsb = STATUS_BADGE[d.status] ?? { kind: 'unknown' as const, label: d.status };
                  return (
                    <div key={i} className="doc-row">
                      <div className={'doc-status-icon ' + d.status}>{d.status === 'ready' ? '✓' : d.status === 'draft' ? '◐' : '·'}</div>
                      <div className="doc-name">{d.name}{d.required && <span className="req">*</span>}</div>
                      <div />
                      <Status kind={dsb.kind} label={dsb.label} />
                    </div>
                  );
                })}
              </div>
              {missing > 0 && <div style={{ marginTop: 8, fontSize: 11, color: 'var(--fail)' }}>{missing} required missing</div>}
            </div>
          </div>
        );
      })}
      <div style={{ display: 'grid', gap: 6 }}>
        <Btn size="lg" variant="primary" icon="share">Share with reviewer</Btn>
        <Btn size="lg" icon="export">Export packet</Btn>
      </div>
    </>
  );
}
