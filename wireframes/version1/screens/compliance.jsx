// Compliance Feasibility screen
const ComplianceScreen = ({ state, setState, run, runStates }) => {
  const c = ABF_DATA.compliance;
  const lot = ABF_DATA.lots.find(l => l.id === state.selectedLotId);
  const planLoading = runStates.plan === 'loading';

  // Group rows by category for visual rhythm
  const groups = c.rows.reduce((acc, r) => {
    (acc[r.category] = acc[r.category] || []).push(r);
    return acc;
  }, {});

  return (
    <React.Fragment>
      <Banner kind="warning" title={`${c.findings} advisory findings — ${c.needsReview} require review or additional data`}>
        This check is a planning screen, not City of Austin approval or a substitute for architect, engineer, surveyor, attorney, arborist, or city review.
      </Banner>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '14px 0 8px' }}>
        <h2 style={{ fontSize: 14, margin: 0 }}>Compliance metrics — {lot ? lot.address : '—'}</h2>
        <span style={{ flex: 1 }} />
        <span className="checkbox"><input type="checkbox" defaultChecked /> Show source / notes</span>
        <span className="checkbox"><input type="checkbox" /> Hide passes</span>
      </div>

      <div className="panel" style={{ overflow: 'hidden' }}>
        <table className="tbl">
          <thead>
            <tr>
              <th className="col-cat">Category</th>
              <th className="col-metric">Metric</th>
              <th>Value</th>
              <th className="col-basis">Basis</th>
              <th className="col-status">Status</th>
              <th className="col-conf">Confidence</th>
              <th className="col-notes">Source / notes</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(groups).flatMap(([cat, rows], gi) =>
              rows.map((r, ri) => (
                <tr key={`${gi}-${ri}`} className={ri === 0 && gi > 0 ? 'sep' : ''}>
                  <td className="col-cat">{ri === 0 ? cat : ''}</td>
                  <td className="col-metric">{r.metric}</td>
                  <td><span className="measure">{r.value}</span></td>
                  <td className="col-basis">{r.basis}</td>
                  <td><Status kind={r.status} /></td>
                  <td><span className="badge neutral"><span className="d"/>{r.confidence}</span></td>
                  <td className="col-notes">{r.notes}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 18 }}>
        <h2 style={{ fontSize: 14, margin: '0 0 10px' }}>Findings</h2>
        <div className="finding-grid">
          <FindingCol kind="passes" title="Passes" items={c.findingsGrouped.passes} />
          <FindingCol kind="warning" title="Warnings" items={c.findingsGrouped.warnings} />
          <FindingCol kind="unknown" title="Unknowns" items={c.findingsGrouped.unknowns} />
          <FindingCol kind="fail" title="Fails" items={c.findingsGrouped.fails} />
        </div>
      </div>

      <div style={{ marginTop: 18, display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <Btn variant="ghost" size="lg" icon="export">Download compliance PDF</Btn>
        <Btn variant="primary" size="lg" iconRight={planLoading ? null : 'arrow-right'} loading={planLoading} onClick={() => run('plan')}>
          Generate schematic plan
        </Btn>
      </div>
    </React.Fragment>
  );
};

const FindingCol = ({ kind, title, items }) => (
  <div className="finding-col">
    <div className="finding-col-h">
      <span className="t">{title}</span>
      <Status kind={kind} label={String(items.length)} />
    </div>
    <div className="finding-col-body">
      {items.length === 0 ? (
        <div style={{ padding: '14px 12px', color: 'var(--text-3)', fontSize: 11.5, textAlign: 'center' }}>none</div>
      ) : items.map((f, i) => (
        <div key={i} className="finding">
          <div className="finding-t">{f.title}</div>
          <div className="finding-b">{f.body}</div>
        </div>
      ))}
    </div>
  </div>
);

window.ComplianceScreen = ComplianceScreen;
