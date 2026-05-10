import { useState } from 'react';
import { useWorkflow } from '../WorkflowContext';
import { Btn, Status, Panel, Banner } from '../components';
import { fmt } from '../components';
import { schematic, lots } from '../data/mock';

function FloorPlanSVG() {
  const W = 100, H = 67;
  const rooms = [
    { x: 0,  y: 0,  w: 7,  h: 21, label: 'Entry porch',      sub: '3.0 × 8.5',  kind: 'circ' },
    { x: 7,  y: 0,  w: 7,  h: 21, label: 'Foyer',            sub: '3.0 × 8.5',  kind: 'circ' },
    { x: 14, y: 0,  w: 43, h: 21, label: 'Living / Dining',  sub: '17.5 × 8.5', kind: 'living' },
    { x: 57, y: 0,  w: 20, h: 21, label: 'Kitchen',          sub: '8.0 × 8.5',  kind: 'service' },
    { x: 77, y: 0,  w: 23, h: 15, label: 'Pantry / Laundry', sub: '9.0 × 6.0',  kind: 'service' },
    { x: 77, y: 15, w: 23, h: 6,  label: 'Powder',           sub: '9.0 × 4.0',  kind: 'bath' },
    { x: 0,  y: 21, w: 36, h: 8,  label: 'Hall',             sub: '14.0 × 3.0', kind: 'circ' },
    { x: 0,  y: 29, w: 36, h: 38, label: 'Bedroom 1',        sub: '14.5 × 15.0', kind: 'sleep' },
    { x: 36, y: 29, w: 23, h: 24, label: 'Bath',             sub: '9.0 × 9.5',  kind: 'bath' },
    { x: 59, y: 29, w: 41, h: 38, label: 'Bedroom 2',        sub: '17.0 × 15.0', kind: 'sleep' },
    { x: 36, y: 53, w: 23, h: 14, label: 'Mech / Storage',   sub: '9.0 × 7.5',  kind: 'service' },
  ];
  const stair = { x: 0, y: 21, w: 8, h: 8 };
  const fill: Record<string, string> = {
    living: 'oklch(0.96 0.02 195)',
    service: 'oklch(0.96 0.02 75)',
    bath: 'oklch(0.96 0.02 240)',
    sleep: 'oklch(0.96 0.02 145)',
    circ: 'oklch(0.97 0.005 90)',
  };
  return (
    <div style={{ aspectRatio: `${W} / ${H}` }}>
      <svg viewBox={`-2 -2 ${W + 4} ${H + 4}`} className="plan-svg" preserveAspectRatio="xMidYMid meet" style={{ background: 'oklch(0.99 0.002 95)' }}>
        <defs>
          <pattern id="grid" width="2" height="2" patternUnits="userSpaceOnUse">
            <path d="M 2 0 L 0 0 0 2" fill="none" stroke="oklch(0.94 0.005 90)" strokeWidth="0.05" />
          </pattern>
        </defs>
        <rect x="-2" y="-2" width={W + 4} height={H + 4} fill="url(#grid)" />
        <rect x="0" y="0" width={W} height={H} fill="white" stroke="var(--text)" strokeWidth="0.6" />
        {rooms.map((r, i) => (
          <g key={i}>
            <rect x={r.x} y={r.y} width={r.w} height={r.h} fill={fill[r.kind]} stroke="var(--text-2)" strokeWidth="0.25" />
            <text x={r.x + r.w / 2} y={r.y + r.h / 2 - 1.2} textAnchor="middle" fontSize="2.2" fontFamily="Geist, sans-serif" fontWeight="500" fill="var(--text)">
              {r.label.toUpperCase()}
            </text>
            <text x={r.x + r.w / 2} y={r.y + r.h / 2 + 2.0} textAnchor="middle" fontSize="1.6" fontFamily="Geist Mono, monospace" fill="var(--text-3)">
              {r.sub} ft
            </text>
          </g>
        ))}
        <g>
          {[0, 1, 2, 3, 4, 5, 6].map(i => (
            <line key={i} x1={stair.x + (i + 0.5)} y1={stair.y} x2={stair.x + (i + 0.5)} y2={stair.y + stair.h} stroke="var(--text-3)" strokeWidth="0.15" />
          ))}
          <text x={stair.x + stair.w / 2} y={stair.y + stair.h + 1.6} textAnchor="middle" fontSize="1.5" fontFamily="Geist Mono, monospace" fill="var(--text-3)">stair → unit B</text>
        </g>
        <g transform={`translate(${W - 6}, ${H - 7})`}>
          <circle r="2.4" fill="white" stroke="var(--text-2)" strokeWidth="0.2" />
          <path d="M 0 -2 L 1 1 L 0 0.4 L -1 1 Z" fill="var(--text)" />
          <text y="3.5" textAnchor="middle" fontSize="1.6" fontFamily="Geist Mono, monospace" fill="var(--text-2)">N</text>
        </g>
        <g transform={`translate(2, ${H - 4})`}>
          <line x1="0" y1="0" x2="20" y2="0" stroke="var(--text)" strokeWidth="0.3" />
          <line x1="0" y1="-0.6" x2="0" y2="0.6" stroke="var(--text)" strokeWidth="0.3" />
          <line x1="10" y1="-0.4" x2="10" y2="0.4" stroke="var(--text)" strokeWidth="0.3" />
          <line x1="20" y1="-0.6" x2="20" y2="0.6" stroke="var(--text)" strokeWidth="0.3" />
          <text x="10" y="-1" textAnchor="middle" fontSize="1.5" fontFamily="Geist Mono, monospace" fill="var(--text-2)">≈ 8 ft</text>
        </g>
      </svg>
    </div>
  );
}

function DesignConversation() {
  const [msgs, setMsgs] = useState([
    { role: 'agent', text: 'Plan generated with 2 quality fails (program fit, unit separation). What direction should I tune?' },
  ]);
  const [val, setVal] = useState('');

  const send = (t?: string) => {
    const text = (t ?? val).trim();
    if (!text) return;
    setMsgs(m => [...m, { role: 'user', text }, { role: 'agent', text: 'Queued for next revision pass — not auto-applied in prototype.' }]);
    setVal('');
  };

  return (
    <Panel title="Design conversation" sub="Future tuning queue" flush>
      <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {msgs.map((m, i) => (
            <div key={i} style={{
              alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '88%',
              padding: '6px 10px',
              border: '1px solid var(--border)',
              background: m.role === 'user' ? 'var(--teal-soft)' : 'var(--panel-alt)',
              borderRadius: 6,
              fontSize: 12,
              color: 'var(--text-2)',
            }}>{m.text}</div>
          ))}
        </div>
        <div className="convo-suggestions">
          {['Make kitchen larger', 'Improve bedroom privacy', 'Add second floor', 'Optimize daylight'].map(s => (
            <button key={s} className="suggestion-chip" onClick={() => send(s)}>{s}</button>
          ))}
        </div>
        <div className="convo-input">
          <input
            className="input"
            placeholder="Ask the schematic agent…"
            value={val}
            onChange={e => setVal(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
          />
          <Btn icon="send" variant="primary" onClick={() => send()}>Send</Btn>
        </div>
      </div>
    </Panel>
  );
}

export function SchematicScreen() {
  const { state, setState, advanceTo } = useWorkflow();
  const s = schematic;
  const lot = lots.find(l => l.id === state.selectedLotId);
  const failed = s.qualityChecks.filter(q => q.status === 'fail').length;

  return (
    <>
      <Banner kind="info" title="Primary schematic plan — conceptual feasibility study">
        Schematic output is conceptual only and not permit-ready architecture. Architect, civil, surveyor, attorney, and city review are required before design reliance.
      </Banner>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 360px', gap: 16, marginTop: 14, alignItems: 'start' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="plan-card">
            <div style={{ padding: '14px 16px', display: 'flex', alignItems: 'center', gap: 12, borderBottom: '1px solid var(--border)' }}>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 600, letterSpacing: '-0.005em' }}>{s.name}</div>
                <div style={{ color: 'var(--text-3)', fontSize: 12, marginTop: 2 }}>
                  {lot ? lot.address : '—'} · revision attempt 3 of 3
                </div>
              </div>
              <span style={{ flex: 1 }} />
              {failed > 0
                ? <Status kind="fail" label={`${failed} quality fails`} />
                : <Status kind="passes" label="Quality OK" />}
              <Btn size="sm" icon="refresh">Regenerate</Btn>
              <Btn size="sm" variant="primary" icon="export">Download SVG</Btn>
            </div>

            <div className="plan-svg-wrap">
              <FloorPlanSVG />
            </div>

            <div className="plan-stats">
              <div className="plan-stat"><div className="plan-stat-l">Target sqft</div><div className="plan-stat-v">{fmt.num(s.targetSqft)}</div></div>
              <div className="plan-stat"><div className="plan-stat-l">Units</div><div className="plan-stat-v">{s.units}</div></div>
              <div className="plan-stat"><div className="plan-stat-l">Quality</div><div className="plan-stat-v" style={{ color: 'var(--fail)' }}>{s.qualityScore}/100</div></div>
              <div className="plan-stat"><div className="plan-stat-l">Status</div><div className="plan-stat-v" style={{ fontFamily: 'var(--font-sans)' }}><Status kind="fail" label="Fails" /></div></div>
            </div>
          </div>

          <Panel title="Room schedule" sub={`${s.rooms.length} rooms · Level 1`} flush>
            <table className="tbl">
              <thead>
                <tr>
                  <th>Room</th>
                  <th style={{ width: 110 }}>Category</th>
                  <th style={{ width: 80 }}>Sqft</th>
                  <th style={{ width: 110 }}>Dimensions</th>
                  <th style={{ width: 70 }}>Level</th>
                </tr>
              </thead>
              <tbody>
                {s.rooms.map((r, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 500 }}>{r.name}</td>
                    <td className="text-2">{r.category}</td>
                    <td><span className="measure">{r.sqft}</span></td>
                    <td><span className="measure">{r.dim}</span></td>
                    <td className="measure">L{r.level}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>

          <Panel title="Quality checks" sub="Deterministic MVP heuristics — not professional architectural validation" flush>
            <div className="qc-list">
              {s.qualityChecks.map((q, i) => (
                <div key={i} className={'qc-row' + (q.status === 'fail' ? ' fail' : '')}>
                  <div className={'qc-mark ' + q.status}>{q.status === 'pass' ? '✓' : '!'}</div>
                  <div>
                    <div className="qc-name">{q.name}</div>
                    <div className="qc-body">{q.body}</div>
                  </div>
                  <Status kind={q.status === 'pass' ? 'passes' : 'fail'} />
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Revision notes" flush>
            <div style={{ padding: 14 }}>
              <ul className="lot-reasons">
                {s.revisionNotes.map((n, i) => <li key={i}>{n}</li>)}
              </ul>
            </div>
          </Panel>
        </div>

        <div className="right-sticky" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <Panel title="Massing summary" flush>
            <div style={{ padding: 14, color: 'var(--text-2)', fontSize: 12, lineHeight: 1.55 }}>
              {s.massing}
            </div>
          </Panel>

          <DesignConversation />

          <Btn
            variant="primary"
            size="lg"
            iconRight="arrow-right"
            onClick={() => advanceTo('packet', 6)}
          >
            Assemble review packet
          </Btn>
        </div>
      </div>
    </>
  );
}
