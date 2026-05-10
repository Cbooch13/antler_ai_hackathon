// Main app: top bar, left rail, screen routing, workflow state machine
const { useState: useS, useEffect: useE } = React;

const STEPS = [
  { key: 'intake',      name: 'Project intake',      short: 'Intake',     icon: 'home',  needs: 0 },
  { key: 'lots',        name: 'Lot discovery',       short: 'Lots',       icon: 'list',  needs: 1 },
  { key: 'lot-context', name: 'Lot context',         short: 'Context',    icon: 'pin',   needs: 2 },
  { key: 'compliance',  name: 'Compliance',          short: 'Compliance', icon: 'shield',needs: 3 },
  { key: 'schematic',   name: 'Primary schematic',   short: 'Schematic',  icon: 'plan',  needs: 4 },
  { key: 'packet',      name: 'Review packet',       short: 'Packet',     icon: 'pkg',   needs: 5 },
];
window.STEPS = STEPS;

const initialState = {
  screen: 'intake',
  step: 1,
  validated: false,
  selectedLotId: null,
  intake: { ...ABF_DATA.intakeDefaults },
  conversation: ABF_DATA.conversationalRequest,
};

const App = () => {
  const [state, setState] = useS(initialState);
  const [runStates, setRunStates] = useS({}); // name -> 'loading' | 'done'
  const [mobile, setMobile] = useS(false);

  // Workflow runner — fakes async stages with realistic latencies.
  const run = (job) => {
    setRunStates(s => ({ ...s, [job]: 'loading' }));
    const after = (ms, fn) => setTimeout(fn, ms);
    if (job === 'validate') {
      after(700, () => { setRunStates(s => ({ ...s, validate: 'done' })); setState(s => ({ ...s, validated: true, step: Math.max(s.step, 1) })); });
    } else if (job === 'normalize') {
      after(900, () => { setRunStates(s => ({ ...s, normalize: 'done' })); setState(s => ({ ...s, validated: true })); });
    } else if (job === 'findLots') {
      after(1500, () => { setRunStates(s => ({ ...s, findLots: 'done' })); setState(s => ({ ...s, screen: 'lots', step: Math.max(s.step, 2) })); });
    } else if (job === 'feasibility') {
      after(1700, () => { setRunStates(s => ({ ...s, feasibility: 'done' })); setState(s => ({ ...s, screen: 'compliance', step: Math.max(s.step, 4) })); });
    } else if (job === 'plan') {
      after(2200, () => { setRunStates(s => ({ ...s, plan: 'done' })); setState(s => ({ ...s, screen: 'schematic', step: Math.max(s.step, 5) })); });
    }
  };

  // Auto-mark steps complete based on user actions
  useE(() => {
    if (state.selectedLotId && state.step < 3) setState(s => ({ ...s, step: 3 }));
  }, [state.selectedLotId]);

  const goTo = (key) => {
    const idx = STEPS.findIndex(s => s.key === key);
    if (idx + 1 > state.step) return; // locked
    setState(s => ({ ...s, screen: key }));
  };

  const screenMeta = STEPS.find(s => s.key === state.screen);
  const Screen = {
    intake: window.IntakeScreen,
    lots: window.LotsScreen,
    'lot-context': window.LotContextScreen,
    compliance: window.ComplianceScreen,
    schematic: window.SchematicScreen,
    packet: window.PacketScreen,
  }[state.screen];

  const screenIsLocked = STEPS.findIndex(s => s.key === state.screen) + 1 > state.step;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">af</div>
          <div className="brand-text">
            <div className="brand-name">Austin Build Feasibility AI</div>
            <div className="brand-sub">stage 0 foundation · v0.7.4</div>
          </div>
        </div>
        <div className="project-meta">
          <span className="project-name">{state.intake.projectName}</span>
          <span className="dot"/>
          <span className="project-id">{ABF_DATA.project.id}</span>
          <span className="dot updated-sep"/>
          <span className="updated" style={{ color: 'var(--text-3)', fontSize: 11.5 }}>updated {ABF_DATA.project.updated}</span>
        </div>
        <span className="advisory-badge"><span className="pulse"/>Advisory<span className="badge-long"> feasibility · not City approval</span></span>
        <div className="topbar-spacer"/>
        <div className="segment mobile-toggle" role="tablist">
          <button role="tab" aria-selected={!mobile} className={!mobile ? 'on' : ''} onClick={() => setMobile(false)}><Icon name="monitor" size={12}/>&nbsp;Desktop</button>
          <button role="tab" aria-selected={mobile} className={mobile ? 'on' : ''} onClick={() => setMobile(true)}><Icon name="phone" size={12}/>&nbsp;Mobile</button>
        </div>
        <div className="topbar-actions">
          <Btn variant="ghost" size="sm" icon="help">Help</Btn>
          <Btn variant="ghost" size="sm" icon="save">Save</Btn>
          <Btn size="sm" icon="export">Export</Btn>
          <Btn size="sm" variant="primary" icon="share">Share</Btn>
        </div>
      </header>

      <div className="body">
        <nav className="rail" aria-label="Workflow">
          <div className="rail-header"><div className="rail-label">Workflow</div></div>
          <div className="rail-list">
            {STEPS.map((s, i) => {
              const num = i + 1;
              const isActive = state.screen === s.key;
              const isComplete = num < state.step;
              const isLocked = num > state.step;
              const cls = ['rail-item'];
              if (isActive) cls.push('active');
              if (isComplete) cls.push('complete');
              if (isLocked) cls.push('locked');
              return (
                <button key={s.key} className={cls.join(' ')} onClick={() => goTo(s.key)} disabled={isLocked} aria-current={isActive ? 'step' : undefined}>
                  <span className="step-num">{isComplete ? <Icon name="check" size={11} stroke={2.4}/> : isLocked ? <Icon name="lock" size={11}/> : num}</span>
                  <span className="step-name">{s.name}</span>
                  <span className="step-status">
                    {isActive && <span style={{ color: 'var(--teal)' }}>now</span>}
                    {isComplete && <span style={{ color: 'var(--text-3)' }}>done</span>}
                  </span>
                </button>
              );
            })}
          </div>
          <div className="rail-foot">
            <div className="rail-foot-line"><span>Owner</span><span className="measure" style={{ color: 'var(--text)' }}>{ABF_DATA.project.owner}</span></div>
            <div className="rail-foot-line"><span>Project</span><span className="measure" style={{ color: 'var(--text)' }}>{ABF_DATA.project.id}</span></div>
            <div className="rail-foot-line"><span>Mode</span><span className="measure" style={{ color: 'var(--text)' }}>advisory</span></div>
          </div>
        </nav>

        <main className="work">
          <div className="work-inner">
            <div className="crumbs">
              <span>Workspace</span>
              <span className="sep">/</span>
              <span>{state.intake.projectName}</span>
              <span className="sep">/</span>
              <span style={{ color: 'var(--text)' }}>{screenMeta.name}</span>
            </div>
            <div className="h-row">
              <div>
                <h1>{screenMeta.name}</h1>
                <div className="sub">{screenSubtitles[state.screen]}</div>
              </div>
              <div className="h-actions">
                {screenActions[state.screen] && screenActions[state.screen]()}
              </div>
            </div>

            {screenIsLocked ? (
              <LockedState
                title={`${screenMeta.name} is locked`}
                body={`Complete the previous steps first. You're currently on step ${state.step} of ${STEPS.length}.`}
                action={<Btn size="sm" iconRight="arrow-right" onClick={() => setState(s => ({ ...s, screen: STEPS[state.step - 1].key }))}>Resume current step</Btn>}
              />
            ) : (
              Screen ? <Screen state={state} setState={setState} run={run} runStates={runStates} /> : null
            )}
          </div>

          <div className="disclaimer-bar">
            <span className="d"/>
            <strong style={{ fontWeight: 600, color: 'var(--text-2)' }}>Advisory feasibility only.</strong>
            <span>This is a planning screen — not City of Austin approval, and not a substitute for architect, engineer, surveyor, attorney, arborist, or city review.</span>
            <span style={{ flex: 1 }}/>
            <span className="kbd">esc</span><span>to dismiss</span>
          </div>
        </main>
      </div>

      {mobile && (
        <div className="mobile-overlay" onClick={(e) => e.target.classList.contains('mobile-overlay') && setMobile(false)}>
          <div className="mobile-shell">
            <div className="mobile-shell-h">
              <Icon name="phone" size={14}/>
              <span>Mobile preview · iPhone 14 Pro</span>
              <span style={{ flex: 1 }}/>
              <button className="btn btn-sm" onClick={() => setMobile(false)}>Close ✕</button>
            </div>
            <IOSFrame width={390} height={780} statusBar={{ time: '2:41', signal: 'wifi' }}>
              <MobileView state={state} setState={setState} run={run} runStates={runStates} onClose={() => setMobile(false)} />
            </IOSFrame>
          </div>
        </div>
      )}
    </div>
  );
};

const screenSubtitles = {
  'intake': 'Capture build specs and produce a validated contract for downstream lot ranking.',
  'lots': 'Ranked candidates from the static prototype dataset. Cross-reference with TCAD before action.',
  'lot-context': 'Selected lot detail, source limitations, and pending official joins.',
  'compliance': 'Advisory metrics across zoning, setbacks, coverage, environmental, permitting, and public safety.',
  'schematic': 'One conceptual schematic plan — not permit-ready architecture.',
  'packet': 'Bundle for licensed reviewers — architect, civil, surveyor, attorney, city official.',
};

const screenActions = {
  'intake': null,
  'lots': () => (
    <React.Fragment>
      <span className="kbd">5 results</span>
      <Btn size="sm" variant="ghost" icon="refresh">Re-rank</Btn>
      <Btn size="sm" icon="list">Filters</Btn>
    </React.Fragment>
  ),
  'lot-context': () => (
    <React.Fragment>
      <Btn size="sm" variant="ghost" icon="refresh">Refresh joins</Btn>
    </React.Fragment>
  ),
  'compliance': () => (
    <React.Fragment>
      <Btn size="sm" variant="ghost">Export CSV</Btn>
    </React.Fragment>
  ),
  'schematic': null,
  'packet': null,
};

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
