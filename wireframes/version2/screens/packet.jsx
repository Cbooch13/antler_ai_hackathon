// Review Packet + Document Vault
const PacketScreen = ({ state, setState }) => {
  const groups = ABF_DATA.packet.groups;

  const totalReq = groups.reduce((acc, g) => acc + g.documents.filter(d => d.required).length, 0);
  const totalReady = groups.reduce((acc, g) => acc + g.documents.filter(d => d.required && d.status === 'ready').length, 0);
  const pct = Math.round((totalReady / totalReq) * 100);

  return (
    <React.Fragment>
      <Banner kind="warning" title="Not official approval">
        Review packet bundles advisory feasibility evidence for licensed reviewers. It is not a substitute for City of Austin approvals.
      </Banner>

      <div style={{ display: 'flex', alignItems: 'center', gap: 14, margin: '14px 0 12px' }}>
        <div style={{ flex: 1, height: 4, background: 'var(--bg-alt)', borderRadius: 2, overflow: 'hidden', border: '1px solid var(--border)' }}>
          <div style={{ width: `${pct}%`, height: '100%', background: 'var(--teal)' }} />
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-2)' }}>
          {totalReady}/{totalReq} required ready · {pct}%
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <Btn icon="export">Export packet</Btn>
          <Btn icon="export">Download SVG plan</Btn>
          <Btn icon="export">Compliance PDF</Btn>
          <Btn icon="share" variant="primary">Share with reviewer</Btn>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {groups.map(g => <ReviewerCard key={g.role} group={g} />)}
      </div>
    </React.Fragment>
  );
};

const STATUS_BADGE = {
  'ready': { kind: 'passes', label: 'Ready' },
  'in-review': { kind: 'info', label: 'In review' },
  'blocked': { kind: 'fail', label: 'Blocked' },
  'not-started': { kind: 'unknown', label: 'Not started' },
  'draft': { kind: 'warning', label: 'Draft' },
  'missing': { kind: 'unknown', label: 'Missing' },
};

const ROLE_SUB = {
  'Architect': 'Design intent & code-rated separation',
  'Civil Engineer': 'Drainage, impervious, site work',
  'Surveyor': 'Boundary, topo, tree survey',
  'Attorney': 'Title, deed, covenant review',
  'City Official': 'Pre-application & overlay checks',
};

const ReviewerCard = ({ group }) => {
  const statusBadge = STATUS_BADGE[group.status];
  const missing = group.documents.filter(d => d.required && d.status === 'missing').length;

  return (
    <div className="reviewer-card">
      <div className="reviewer-h">
        <div style={{ width: 26, height: 26, borderRadius: 4, background: 'var(--bg-alt)', border: '1px solid var(--border)', display: 'grid', placeItems: 'center', color: 'var(--text-2)' }}>
          <RoleIcon role={group.role} />
        </div>
        <div style={{ minWidth: 0 }}>
          <div className="role">{group.role}</div>
          <div className="role-sub">{ROLE_SUB[group.role]}</div>
        </div>
        <span style={{ flex: 1 }} />
        {missing > 0 && <Status kind="warning" label={`${missing} missing`} />}
        <Status kind={statusBadge.kind} label={statusBadge.label} />
        <Btn size="sm" variant="ghost" icon="send">Notify</Btn>
      </div>
      <div className="reviewer-body">
        <div>
          <div className="label" style={{ marginBottom: 4 }}>Required documents</div>
          <div className="doc-list">
            {group.documents.map((d, i) => {
              const sb = STATUS_BADGE[d.status];
              return (
                <div key={i} className="doc-row">
                  <div className={'doc-status-icon ' + d.status}>
                    {d.status === 'ready' ? '✓' : d.status === 'draft' ? '◐' : '·'}
                  </div>
                  <div>
                    <div className="doc-name">{d.name}{d.required && <span className="req">*</span>}</div>
                    {d.file && <div className="doc-file">{d.file}</div>}
                  </div>
                  <Status kind={sb.kind} label={sb.label} />
                  <Btn size="sm" variant="ghost">{d.file ? 'View' : 'Upload'}</Btn>
                </div>
              );
            })}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div>
            <div className="label" style={{ marginBottom: 4 }}>Notes</div>
            <div className="notes-box">{group.notes}</div>
          </div>
          <div>
            <div className="label" style={{ marginBottom: 4 }}>Add files</div>
            <div className="upload-zone">Drop files here or click to upload</div>
          </div>
          <div>
            <div className="label" style={{ marginBottom: 4 }}>Reviewer comments</div>
            <textarea className="textarea" rows={2} placeholder={`Add comment for ${group.role.toLowerCase()}…`} />
          </div>
        </div>
      </div>
    </div>
  );
};

const RoleIcon = ({ role }) => {
  if (role === 'Architect') return <Icon name="plan" size={14}/>;
  if (role === 'Civil Engineer') return <Icon name="water" size={14}/>;
  if (role === 'Surveyor') return <Icon name="map" size={14}/>;
  if (role === 'Attorney') return <Icon name="shield" size={14}/>;
  if (role === 'City Official') return <Icon name="tag" size={14}/>;
  return <Icon name="doc" size={14}/>;
};

window.PacketScreen = PacketScreen;
