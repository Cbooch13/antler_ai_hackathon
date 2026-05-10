import { useState, useEffect, useCallback } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { WorkflowContext } from './WorkflowContext';
import { Icon, Btn, LockedState } from './components';
import { MobilePreview } from './mobile/MobilePreview';
import { IosFrame } from './components/IosFrame';
import * as validate from './api/validate';
import * as normalize from './api/normalize';
import * as findLots from './api/findLots';
import * as feasibility from './api/feasibility';
import * as plan from './api/plan';
import * as mock from './data/mock';
import type { WorkflowState, Screen, JobName, RunStates } from './types';

export const STEPS = [
  { key: 'intake' as Screen,      name: 'Project intake',    short: 'Intake',     needs: 0 },
  { key: 'lots' as Screen,        name: 'Lot discovery',     short: 'Lots',       needs: 1 },
  { key: 'lot-context' as Screen, name: 'Lot context',       short: 'Context',    needs: 2 },
  { key: 'compliance' as Screen,  name: 'Compliance',        short: 'Compliance', needs: 3 },
  { key: 'schematic' as Screen,   name: 'Primary schematic', short: 'Schematic',  needs: 4 },
  { key: 'packet' as Screen,      name: 'Review packet',     short: 'Packet',     needs: 5 },
];

const SCREEN_SUBS: Record<Screen, string> = {
  'intake':      'Capture build specs and produce a validated contract for downstream lot ranking.',
  'lots':        'Ranked candidates from the static prototype dataset. Cross-reference with TCAD before action.',
  'lot-context': 'Selected lot detail, source limitations, and pending official joins.',
  'compliance':  'Advisory metrics across zoning, setbacks, coverage, environmental, permitting, and public safety.',
  'schematic':   'One conceptual schematic plan — not permit-ready architecture.',
  'packet':      'Bundle for licensed reviewers — architect, civil, surveyor, attorney, city official.',
};

const initialState: WorkflowState = {
  screen: 'intake',
  step: 1,
  validated: false,
  selectedLotId: null,
  intake: { ...mock.intakeDefaults },
  conversation: mock.conversationalRequest,
};

function urlToScreen(pathname: string): Screen {
  const seg = pathname.split('/').pop() as Screen;
  const known: Screen[] = ['intake', 'lots', 'lot-context', 'compliance', 'schematic', 'packet'];
  return known.includes(seg) ? seg : 'intake';
}

export function WorkspaceShell() {
  const navigate = useNavigate();
  const location = useLocation();
  const [state, setState] = useState<WorkflowState>(initialState);
  const [runStates, setRunStates] = useState<RunStates>({});
  const [showMobile, setShowMobile] = useState(false);

  // Sync state.screen from URL pathname
  useEffect(() => {
    const screen = urlToScreen(location.pathname);
    setState(s => ({ ...s, screen }));
  }, [location.pathname]);

  // Advance to lot-context when a lot is selected
  useEffect(() => {
    if (state.selectedLotId && state.step < 3) {
      setState(s => ({ ...s, step: 3 }));
    }
  }, [state.selectedLotId, state.step]);

  const goTo = useCallback((key: Screen) => {
    const idx = STEPS.findIndex(s => s.key === key);
    if (idx + 1 > state.step) return;
    navigate(`/workspace/${key}`);
  }, [state.step, navigate]);

  const advanceTo = useCallback((key: Screen, minStep: number) => {
    setState(s => ({ ...s, step: Math.max(s.step, minStep) }));
    navigate(`/workspace/${key}`);
  }, [navigate]);

  const run = useCallback((job: JobName) => {
    setRunStates(s => ({ ...s, [job]: 'loading' }));
    const delay = (ms: number) => new Promise<void>(res => setTimeout(res, ms));

    if (job === 'validate') {
      delay(700).then(() => validate.run(state.intake)).then(() => {
        setRunStates(s => ({ ...s, validate: 'done' }));
        setState(s => ({ ...s, validated: true, step: Math.max(s.step, 1) }));
      });
    } else if (job === 'normalize') {
      delay(900).then(() => normalize.run(state.conversation)).then(() => {
        setRunStates(s => ({ ...s, normalize: 'done' }));
        setState(s => ({ ...s, validated: true }));
      });
    } else if (job === 'findLots') {
      delay(1500).then(() => findLots.run(state.intake)).then(() => {
        setRunStates(s => ({ ...s, findLots: 'done' }));
        setState(s => ({ ...s, step: Math.max(s.step, 2) }));
        navigate('/workspace/lots');
      });
    } else if (job === 'feasibility') {
      delay(1700).then(() => feasibility.run(state.selectedLotId)).then(() => {
        setRunStates(s => ({ ...s, feasibility: 'done' }));
        setState(s => ({ ...s, step: Math.max(s.step, 4) }));
        navigate('/workspace/compliance');
      });
    } else if (job === 'plan') {
      delay(2200).then(() => plan.run(state.selectedLotId)).then(() => {
        setRunStates(s => ({ ...s, plan: 'done' }));
        setState(s => ({ ...s, step: Math.max(s.step, 5) }));
        navigate('/workspace/schematic');
      });
    }
  }, [state, navigate]);

  const currentScreen = urlToScreen(location.pathname);
  const screenMeta = STEPS.find(s => s.key === currentScreen) ?? STEPS[0];
  const screenIdx = STEPS.findIndex(s => s.key === currentScreen);
  const screenIsLocked = screenIdx + 1 > state.step;

  const screenActions: Partial<Record<Screen, React.ReactNode>> = {
    lots: (
      <>
        <span className="kbd">5 results</span>
        <Btn size="sm" variant="ghost" icon="refresh">Re-rank</Btn>
        <Btn size="sm" icon="list">Filters</Btn>
      </>
    ),
    'lot-context': <Btn size="sm" variant="ghost" icon="refresh">Refresh joins</Btn>,
    compliance: <Btn size="sm" variant="ghost">Export CSV</Btn>,
  };

  return (
    <WorkflowContext.Provider value={{ state, setState, run, runStates, goTo, advanceTo }}>
      <div className="app">
        <header className="topbar">
          <button
            className="brand"
            style={{ border: 0, borderRight: '1px solid var(--border)', background: 'transparent', cursor: 'pointer', padding: '0 18px 0 0' }}
            onClick={() => navigate('/')}
            title="Back to landing"
          >
            <div className="brand-mark">af</div>
            <div className="brand-text">
              <div className="brand-name">Austin Build Feasibility</div>
              <div className="brand-sub">stage 0 · v0.7.4</div>
            </div>
          </button>
          <div className="project-meta">
            <span className="project-name">{state.intake.projectName}</span>
            <span className="dot" />
            <span className="project-id">{mock.project.id}</span>
            <span className="dot updated-sep" />
            <span className="updated" style={{ color: 'var(--text-3)', fontSize: 11.5 }}>updated {mock.project.updated}</span>
          </div>
          <span className="advisory-badge">
            <span className="pulse" />
            Advisory<span className="badge-long"> · not City approval</span>
          </span>
          <div className="topbar-spacer" />
          <div className="segment mobile-toggle" role="tablist">
            <button role="tab" aria-selected={!showMobile} className={!showMobile ? 'on' : ''} onClick={() => setShowMobile(false)}>
              <Icon name="monitor" size={12} />&nbsp;Desktop
            </button>
            <button role="tab" aria-selected={showMobile} className={showMobile ? 'on' : ''} onClick={() => setShowMobile(true)}>
              <Icon name="phone" size={12} />&nbsp;Mobile
            </button>
          </div>
          <div className="topbar-actions">
            <Btn variant="ghost" size="sm" icon="help"><span className="label-text">Help</span></Btn>
            <Btn variant="ghost" size="sm" icon="save"><span className="label-text">Save</span></Btn>
            <Btn size="sm" icon="export"><span className="label-text">Export</span></Btn>
            <Btn size="sm" variant="primary" icon="share"><span className="label-text">Share</span></Btn>
          </div>
        </header>

        <div className="body">
          <nav className="rail" aria-label="Workflow">
            <div className="rail-header"><div className="rail-label">Workflow</div></div>
            <div className="rail-list">
              {STEPS.map((s, i) => {
                const num = i + 1;
                const isActive = currentScreen === s.key;
                const isComplete = num < state.step;
                const isLocked = num > state.step;
                const cls = ['rail-item'];
                if (isActive) cls.push('active');
                if (isComplete) cls.push('complete');
                if (isLocked) cls.push('locked');
                return (
                  <button
                    key={s.key}
                    className={cls.join(' ')}
                    onClick={() => goTo(s.key)}
                    disabled={isLocked}
                    aria-current={isActive ? 'step' : undefined}
                  >
                    <span className="step-num">
                      {isComplete ? <Icon name="check" size={11} stroke={2.4} /> : isLocked ? <Icon name="lock" size={11} /> : num}
                    </span>
                    <span className="step-name">{s.name}</span>
                    <span className="step-status">
                      {isActive && <span>now</span>}
                      {isComplete && <span style={{ color: 'var(--text-3)' }}>done</span>}
                    </span>
                  </button>
                );
              })}
            </div>
            <div className="rail-foot">
              <div className="rail-foot-line"><span>Owner</span><span style={{ color: 'var(--text)' }}>{mock.project.owner}</span></div>
              <div className="rail-foot-line"><span>Project</span><span style={{ color: 'var(--text)' }}>{mock.project.id}</span></div>
              <div className="rail-foot-line"><span>Mode</span><span style={{ color: 'var(--text)' }}>advisory</span></div>
            </div>
          </nav>

          <main className="work">
            <div className="work-inner">
              <div className="crumbs">
                <span style={{ cursor: 'pointer' }} onClick={() => navigate('/')}>Workspace</span>
                <span className="sep">/</span>
                <span>{state.intake.projectName}</span>
                <span className="sep">/</span>
                <span style={{ color: 'var(--text)' }}>{screenMeta.name}</span>
              </div>
              <div className="h-row">
                <div>
                  <h1>{screenMeta.name}</h1>
                  <div className="sub">{SCREEN_SUBS[currentScreen]}</div>
                </div>
                <div className="h-actions">
                  {screenActions[currentScreen]}
                </div>
              </div>

              {screenIsLocked ? (
                <LockedState
                  title={`${screenMeta.name} is locked`}
                  body={`Complete the previous steps first. You're currently on step ${state.step} of ${STEPS.length}.`}
                  action={
                    <Btn size="sm" iconRight="arrow-right" onClick={() => navigate(`/workspace/${STEPS[state.step - 1].key}`)}>
                      Resume current step
                    </Btn>
                  }
                />
              ) : (
                <Outlet />
              )}
            </div>

            <div className="disclaimer-bar">
              <span className="d" />
              <strong style={{ fontWeight: 600, color: 'var(--text-2)' }}>Advisory feasibility only.</strong>
              <span>Not City of Austin approval, and not a substitute for architect, engineer, surveyor, attorney, arborist, or city review.</span>
              <span style={{ flex: 1 }} />
              <span className="kbd">esc</span><span>to dismiss</span>
            </div>
          </main>
        </div>

        {showMobile && (
          <div
            className="mobile-overlay"
            onClick={(e) => {
              if ((e.target as HTMLElement).classList.contains('mobile-overlay')) setShowMobile(false);
            }}
          >
            <div className="mobile-shell">
              <div className="mobile-shell-h">
                <Icon name="phone" size={14} />
                <span>Mobile preview · iPhone 14 Pro</span>
                <span style={{ flex: 1 }} />
                <button className="btn btn-sm" onClick={() => setShowMobile(false)}>Close ✕</button>
              </div>
              <IosFrame width={390} height={780} time="2:41">
                <MobilePreview
                  state={state}
                  setState={setState}
                  run={run}
                  onClose={() => setShowMobile(false)}
                />
              </IosFrame>
            </div>
          </div>
        )}
      </div>
    </WorkflowContext.Provider>
  );
}
