// Lot Discovery screen
const LotsScreen = ({ state, setState, run, runStates }) => {
  const lots = ABF_DATA.lots;
  const select = (id) => setState(s => ({ ...s, selectedLotId: id, step: Math.max(s.step, 2) }));

  const isLoading = runStates.findLots === 'loading';

  if (isLoading) {
    return (
      <div className="card-list">
        {[0,1,2,3].map(i => (
          <div key={i} className="lot-card" style={{ cursor: 'default' }}>
            <Skel h={110} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <Skel h={18} w="70%"/>
              <Skel h={12} w="50%"/>
              <Skel h={12} w="40%"/>
              <Skel h={12} w="80%"/>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8 }}>
              <Skel h={24} w={70}/>
              <Skel h={20} w={120}/>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <React.Fragment>
      <Banner kind="warning" title="Prototype / static dataset — not current inventory">
        Results come from a static Kaggle prototype dataset. Cross-reference parcel/property identity with Travis County / TCAD or official records before any acquisition decisions.
      </Banner>

      <div className="card-list" style={{ marginTop: 12 }}>
        {lots.map((l, i) => {
          const selected = state.selectedLotId === l.id;
          return (
            <div key={l.id} className={'lot-card' + (selected ? ' selected' : '')} onClick={() => select(l.id)}>
              <div className="lot-thumb">
                <div style={{ textAlign: 'center', lineHeight: 1.4 }}>
                  parcel · aerial<br/>
                  <span style={{ color: 'var(--text-4)' }}>placeholder</span>
                </div>
              </div>
              <div style={{ minWidth: 0 }}>
                <div className="lot-meta-row">
                  <span style={{ color: 'var(--text-3)' }}>RANK #{i + 1}</span>
                  <span className="dot" />
                  <span className="lot-prototype-tag">prototype/static dataset · not current inventory</span>
                </div>
                <div className="lot-addr" style={{ marginTop: 4 }}>{l.address}</div>
                <div className="lot-neighborhood">{l.city} · {l.neighborhood}</div>
                <div className="lot-stats">
                  <div className="ls"><span className="ls-l">Price</span><span className="ls-v"><span className="mono">{fmt.money(l.price)}</span></span></div>
                  <div className="ls"><span className="ls-l">Lot</span><span className="ls-v"><span className="mono">{fmt.num(l.lotSqft)}</span> sqft</span></div>
                  <div className="ls"><span className="ls-l">Building</span><span className="ls-v">{l.buildingSqft ? <React.Fragment><span className="mono">{fmt.num(l.buildingSqft)}</span> sqft</React.Fragment> : <span className="muted">—</span>}</span></div>
                  <div className="ls"><span className="ls-l">Beds / Baths</span><span className="ls-v measure">{l.beds} / {l.baths}</span></div>
                  <div className="ls"><span className="ls-l">Units</span><span className="ls-v measure">{l.units}</span></div>
                </div>
                <ul className="lot-reasons">
                  {l.reasons.map((r, j) => <li key={j}>{r}</li>)}
                </ul>
              </div>
              <div className="lot-score-block">
                <div className="lot-score">{l.score.toFixed(l.score === 100 ? 0 : 2)}<span className="total">/100</span></div>
                {selected
                  ? <Status kind="info" label="Selected" />
                  : <Btn size="sm" iconRight="chevron-r" onClick={(e) => { e.stopPropagation(); select(l.id); }}>View context</Btn>}
              </div>
            </div>
          );
        })}
      </div>
    </React.Fragment>
  );
};

window.LotsScreen = LotsScreen;
