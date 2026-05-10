// Lot Context — v2 with aerial photo placeholder
const LotContextScreenV2 = ({ state, setState, run, runStates }) => {
  const lot = ABF_DATA.lots.find(l => l.id === state.selectedLotId);
  if (!lot) {
    return <LockedState title="No lot selected" body="Pick a candidate from Lot Discovery to load its parcel context, sources, and warnings." action={<Btn size="sm" onClick={() => setState(s => ({ ...s, screen: 'lots' }))}>Go to Lot Discovery</Btn>} />;
  }
  const photo = window.ABF_PHOTOS.aerials[lot.id];
  const mapUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(lot.address + ', ' + lot.city)}`;
  const feasibilityLoading = runStates.feasibility === 'loading';

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 380px', gap: 24 }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <Panel
          title={lot.address}
          sub={lot.city + ' · ' + lot.neighborhood}
          badge={<span className="lot-prototype-tag" style={{ marginLeft: 6 }}>prototype · static dataset</span>}
          flush
        >
          <div className="map-placeholder" style={{ borderRadius: 0, border: 0, height: 360, backgroundImage: `url(${photo})` }}>
            <div className="map-overlay">
              <div><strong>{lot.address}</strong></div>
              <div>{lot.coords.lat.toFixed(4)}, {lot.coords.lng.toFixed(4)}</div>
            </div>
            <div className="map-pin" />
            <div className="map-attribution">aerial preview · placeholder imagery</div>
          </div>
          <div style={{ padding: 16, display: 'flex', alignItems: 'center', gap: 8, borderTop: '1px solid var(--border)' }}>
            <a className="btn btn-sm" href={mapUrl} target="_blank" rel="noreferrer"><Icon name="map" size={13}/>&nbsp;Open in Maps</a>
            <a className="btn btn-sm" href={`https://www.google.com/maps?layer=c&cbll=${lot.coords.lat},${lot.coords.lng}`} target="_blank" rel="noreferrer">Street view</a>
            <span style={{ flex: 1 }} />
            <span className="kbd">Mapbox token not configured</span>
          </div>
        </Panel>

        <Panel title="Source limitations & joins" flush>
          <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
            <Banner kind="warning" title="Official parcel join pending">
              No official parcel ID is attached to this static fallback row yet — TCAD lookup required.
            </Banner>
            <Banner kind="warning" title="Zoning feature not joined">
              No zoning feature has been joined. Setbacks, height, and FAR are SF-3-style estimates only.
            </Banner>
            <Banner kind="warning" title="Permit history not joined">
              Public permit records (Austin Open Data) have not been linked to this prototype row.
            </Banner>
            <Banner kind="neutral" title="Aerial imagery placeholder">
              Imagery shown is editorial placeholder. Replace with licensed Mapbox / Nearmap before review handoff.
            </Banner>
          </div>
        </Panel>
      </div>

      <div className="right-sticky" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <Panel title="Parcel summary" flush>
          <div style={{ padding: 16 }}>
            <div className="kvs">
              <div className="k">Address</div><div className="v">{lot.address}</div>
              <div className="k">City</div><div className="v">{lot.city}</div>
              <div className="k">Neighborhood</div><div className="v">{lot.neighborhood}</div>
              <div className="k">Coordinates</div><div className="v">{lot.coords.lat.toFixed(4)}, {lot.coords.lng.toFixed(4)}</div>
              <div className="k">Price</div><div className="v">{fmt.money(lot.price)}</div>
              <div className="k">Lot sqft</div><div className="v">{fmt.num(lot.lotSqft)}</div>
              <div className="k">Building sqft</div><div className="v">{lot.buildingSqft ? fmt.num(lot.buildingSqft) : '—'}</div>
              <div className="k">Beds / Baths</div><div className="v">{lot.beds} / {lot.baths}</div>
              <div className="k">Units</div><div className="v">{lot.units}</div>
              <div className="k">Score</div><div className="v">{lot.score.toFixed(2)} / 100</div>
            </div>
          </div>
        </Panel>

        <Panel title="Source metadata" flush>
          <div style={{ padding: 16 }}>
            <div className="kvs">
              <div className="k">Source</div><div className="v">kaggle.static.fallback</div>
              <div className="k">Row id</div><div className="v">austin_homes/04307</div>
              <div className="k">As of</div><div className="v">2024-08-12</div>
              <div className="k">Parcel id</div><div className="v"><span className="muted">pending</span></div>
              <div className="k">Zoning</div><div className="v"><span className="muted">pending</span></div>
              <div className="k">Permits</div><div className="v"><span className="muted">pending</span></div>
            </div>
          </div>
        </Panel>

        <Btn size="lg" variant="primary" iconRight={feasibilityLoading ? null : 'arrow-right'} loading={feasibilityLoading} onClick={() => run('feasibility')}>
          Run feasibility check
        </Btn>
      </div>
    </div>
  );
};
window.LotContextScreenV2 = LotContextScreenV2;
