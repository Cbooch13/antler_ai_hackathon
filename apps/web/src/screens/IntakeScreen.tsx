import { useWorkflow } from '../WorkflowContext';
import { Btn, Status, Panel, Banner, JsonView, Skel } from '../components';
import * as mock from '../data/mock';

export function IntakeScreen() {
  const { state, setState, run, runStates } = useWorkflow();
  const intake = state.intake;
  const updateIntake = (key: keyof typeof intake, value: unknown) =>
    setState(s => ({ ...s, intake: { ...s.intake, [key]: value } }));
  const removeStyle = (style: string) =>
    updateIntake('stylePreferences', intake.stylePreferences.filter(s => s !== style));

  const validated = state.validated;
  const findLotsLoading = runStates.findLots === 'loading';
  const validateLoading = runStates.validate === 'loading';
  const normalizeLoading = runStates.normalize === 'loading';

  return (
    <div className="workspace-2col">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <Panel
          title="Project intake"
          sub="Structured spec — used to score lots, generate plans, and assemble the review packet."
          action={
            <div style={{ display: 'flex', gap: 6 }}>
              <Btn size="sm" variant="ghost" icon="refresh">Reset</Btn>
              <Btn size="sm" icon="check" loading={validateLoading} onClick={() => run('validate')}>
                Validate spec
              </Btn>
            </div>
          }
        >
          <div className="form-grid">
            <div className="field field-full">
              <label className="label">Project name</label>
              <input className="input" value={intake.projectName} onChange={e => updateIntake('projectName', e.target.value)} />
            </div>
            <div className="field">
              <label className="label">Property type</label>
              <select className="select" value={intake.propertyType} onChange={e => updateIntake('propertyType', e.target.value)}>
                <option>ADU</option>
                <option>Single-family residence</option>
                <option>Duplex</option>
                <option>Townhome</option>
                <option>Small multifamily</option>
              </select>
            </div>
            <div className="field">
              <label className="label">Risk tolerance</label>
              <div className="segment" role="radiogroup">
                {['Low', 'Medium', 'High'].map(t => (
                  <button
                    key={t}
                    role="radio"
                    aria-checked={intake.riskTolerance === t}
                    className={intake.riskTolerance === t ? 'on' : ''}
                    onClick={() => updateIntake('riskTolerance', t)}
                  >{t}</button>
                ))}
              </div>
            </div>
            <div className="field">
              <label className="label">Budget</label>
              <div className="input-prefix">
                <span className="pre">USD</span>
                <input className="input mono" type="number" value={intake.budget} onChange={e => updateIntake('budget', +e.target.value)} />
              </div>
            </div>
            <div className="field">
              <label className="label">Units</label>
              <input className="input mono" type="number" value={intake.units} onChange={e => updateIntake('units', +e.target.value)} />
            </div>
            <div className="field">
              <label className="label">Target lot sqft</label>
              <input className="input mono" type="number" value={intake.lotSqft} onChange={e => updateIntake('lotSqft', +e.target.value)} />
            </div>
            <div className="field">
              <label className="label">Target building sqft</label>
              <input className="input mono" type="number" value={intake.buildingSqft} onChange={e => updateIntake('buildingSqft', +e.target.value)} />
            </div>
            <div className="field">
              <label className="label">Bedrooms</label>
              <input className="input mono" type="number" value={intake.beds} onChange={e => updateIntake('beds', +e.target.value)} />
            </div>
            <div className="field">
              <label className="label">Bathrooms</label>
              <input className="input mono" type="number" value={intake.baths} onChange={e => updateIntake('baths', +e.target.value)} />
            </div>
            <div className="field field-full">
              <label className="label">Style preferences</label>
              <div className="chip-row">
                {intake.stylePreferences.map(s => (
                  <span key={s} className="chip removable">
                    {s}<button onClick={() => removeStyle(s)} aria-label={`Remove ${s}`}>×</button>
                  </span>
                ))}
                <button className="chip" style={{ cursor: 'pointer', borderStyle: 'dashed', color: 'var(--text-3)' }}>+ Add tag</button>
              </div>
              <span className="help">Tags inform plan-generation prompts and lot ranking weights.</span>
            </div>
          </div>
        </Panel>

        <Panel
          title="Conversational request"
          sub="Free-text intent — normalized into the spec via parser or LLM."
          action={
            <Btn size="sm" icon="refresh" loading={normalizeLoading} onClick={() => run('normalize')}>
              Normalize request
            </Btn>
          }
        >
          <textarea
            className="textarea"
            value={state.conversation}
            onChange={e => setState(s => ({ ...s, conversation: e.target.value }))}
            rows={3}
          />
          <div style={{ marginTop: 8, fontSize: 11.5, color: 'var(--text-3)' }}>
            Falls back to local parser when LLM_NORMALIZER_ENABLED=false.
          </div>
        </Panel>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="help">Spec is locally validated. Find lots when ready.</span>
          <div style={{ display: 'flex', gap: 8 }}>
            <Btn size="lg" variant="ghost" iconRight="chevron-r">Save draft</Btn>
            <Btn
              size="lg"
              variant="primary"
              loading={findLotsLoading}
              iconRight={findLotsLoading ? null : 'arrow-right'}
              onClick={() => run('findLots')}
              disabled={!validated}
            >
              Find prototype lots
            </Btn>
          </div>
        </div>
      </div>

      <div className="right-sticky" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <Panel
          title="Validated contract"
          badge={validated ? <Status kind="passes" label="Validated" /> : <Status kind="unknown" label="Pending" />}
          sub="Normalized JSON"
          flush
        >
          <div style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 12 }}>
            {validateLoading ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <Skel h={16} w="60%" />
                <Skel h={120} />
                <Skel h={14} w="40%" />
              </div>
            ) : (
              <>
                <JsonView data={mock.validatedContract.spec} />
                <div>
                  <div className="label" style={{ marginBottom: 4 }}>Missing fields</div>
                  {mock.validatedContract.missingFields.length === 0
                    ? <Status kind="passes" label="None" />
                    : <Status kind="warning" label={`${mock.validatedContract.missingFields.length} missing`} />}
                </div>
                <div>
                  <div className="label" style={{ marginBottom: 4 }}>Assumptions</div>
                  <ul className="lot-reasons">
                    {mock.validatedContract.assumptions.map((a, i) => <li key={i}>{a}</li>)}
                  </ul>
                </div>
                {mock.validatedContract.warnings.length > 0 && (
                  <div>
                    <div className="label" style={{ marginBottom: 4 }}>Warnings</div>
                    {mock.validatedContract.warnings.map((w, i) => (
                      <Banner key={i} kind="warning" title={w} />
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}
