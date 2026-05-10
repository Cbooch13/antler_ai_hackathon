// Lot Discovery — v2 image-led cards
const LotsScreenV2 = ({ state, setState, run, runStates }) => {
  const lots = ABF_DATA.lots;
  const photos = window.ABF_PHOTOS.lots;
  const select = (id) => setState(s => ({ ...s, selectedLotId: id, step: Math.max(s.step, 2) }));
  const isLoading = runStates.findLots === 'loading';

  if (isLoading) {
    return (
      <div className="card-list">
        {[0,1,2,3].map(i => (
          <div key={i} className="lot-card" style={{ cursor: 'default' }}>
            <div className="lot-thumb" style={{ background: 'var(--bg-warm)' }}><Skel h={'100%'} w="100%" style={{ borderRadius: 0 }} /></div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '18px 0' }}>
              <Skel h={22} w="60%"/>
              <Skel h={12} w="40%"/>
              <Skel h={12} w="80%"/>
              <Skel h={12} w="65%"/>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 10, padding: '18px 22px 18px 0' }}>
              <Skel h={36} w={90}/>
              <Skel h={24} w={120}/>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <React.Fragment>
      <Banner kind="warning" title="Prototype / static dataset — not current inventory">
        Results come from a static Kaggle prototype dataset. Cross-reference parcel and property identity with Travis County / TCAD or official records before any acquisition decisions.
      </Banner>

      <div className="card-list" style={{ marginTop: 16 }}>
        {lots.map((l, i) => {
          const selected = state.selectedLotId === l.id;
          const photo = photos[l.id];
          return (
            <div key={l.id} className={'lot-card' + (selected ? ' selected' : '')} onClick={() => select(l.id)}>
              <div className="lot-thumb" style={{ backgroundImage: `url(${photo})` }}>
                <div className="lot-thumb-tag">Rank #{i + 1}</div>
              </div>
              <div className="lot-card-body">
                <div className="lot-meta-row">
                  <span>{l.neighborhood}</span>
                  <span className="dot"/>
                  <span className="lot-prototype-tag">prototype · static dataset</span>
                </div>
                <div className="lot-addr">{l.address}</div>
                <div className="lot-neighborhood">{l.city}</div>
                <div className="lot-stats">
                  <div className="ls"><span className="ls-l">Price</span><span className="ls-v"><span className="mono">{fmt.money(l.price)}</span></span></div>
                  <div className="ls"><span className="ls-l">Lot</span><span className="ls-v"><span className="mono">{fmt.num(l.lotSqft)}</span> sqft</span></div>
                  <div className="ls"><span className="ls-l">Building</span><span className="ls-v">{l.buildingSqft ? <React.Fragment><span className="mono">{fmt.num(l.buildingSqft)}</span> sqft</React.Fragment> : <span className="muted">—</span>}</span></div>
                  <div className="ls"><span className="ls-l">Beds · Baths</span><span className="ls-v measure">{l.beds} · {l.baths}</span></div>
                  <div className="ls"><span className="ls-l">Units</span><span className="ls-v measure">{l.units}</span></div>
                </div>
                <ul className="lot-reasons">
                  {l.reasons.slice(0, 3).map((r, j) => <li key={j}>{r}</li>)}
                </ul>
              </div>
              <div className="lot-score-block">
                <div className="lot-score">{l.score.toFixed(l.score === 100 ? 0 : 1)}<span className="total"> / 100</span></div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-end' }}>
                  {selected
                    ? <Status kind="info" label="Selected" />
                    : <Btn size="sm" iconRight="chevron-r" onClick={(e) => { e.stopPropagation(); select(l.id); }}>View context</Btn>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </React.Fragment>
  );
};
window.LotsScreenV2 = LotsScreenV2;
