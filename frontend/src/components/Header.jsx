import React from 'react';
import { Play, ShieldCheck, Zap, RotateCcw } from 'lucide-react';

export default function Header({
  selectedMerchant,
  setSelectedMerchant,
  demoStage,
  onRunGuidedDemo,
  onResetDemo,
  onJumpToPerformance
}) {
  const merchants = [
    'ALL',
    ...Array.from({ length: 20 }, (_, i) => `merch_${(i + 1).toString().padStart(2, '0')}`)
  ];

  return (
    <header className="top-header">
      <div className="header-left">
        <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
          Merchant:
        </label>
        <select
          className="merchant-select"
          value={selectedMerchant}
          onChange={(e) => setSelectedMerchant(e.target.value)}
        >
          {merchants.map((m) => (
            <option key={m} value={m}>
              {m === 'ALL' ? 'All Merchants (20 Active)' : m}
            </option>
          ))}
        </select>

        <div className="status-pill">
          <span className="status-dot"></span>
          <span>Sentinel Online (RF | p*=0.25 | Held-Out Test)</span>
        </div>

        <span className="badge badge-dev" style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem' }}>
          Synthetic Benchmark Data
        </span>
      </div>

      <div className="demo-controls">
        <button className="btn-demo btn-demo-primary" onClick={onRunGuidedDemo}>
          <Zap size={14} style={{ marginRight: '0.3rem', display: 'inline' }} />
          Guided 3-Stage Pitch Demo
        </button>

        <button className="btn-demo" onClick={onResetDemo}>
          <RotateCcw size={14} style={{ marginRight: '0.3rem', display: 'inline' }} />
          Reset Demo
        </button>

        <button className="btn-demo" onClick={onJumpToPerformance}>
          Held-Out Metrics
        </button>
      </div>
    </header>
  );
}
