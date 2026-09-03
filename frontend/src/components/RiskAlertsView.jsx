import React, { useState, useEffect } from 'react';
import { ShieldAlert, AlertTriangle, Zap, CheckCircle2 } from 'lucide-react';

export default function RiskAlertsView({ onSelectTxn }) {
  const [spikes, setSpikes] = useState([]);

  useEffect(() => {
    async function fetchAlerts() {
      try {
        const res = await fetch('/api/v1/risk/merchant-spikes');
        if (res.ok) setSpikes(await res.json());
      } catch (err) {
        console.error('Error fetching alerts:', err);
      }
    }
    fetchAlerts();
  }, []);

  const activeSpikes = spikes.filter(s => s.is_spike_alert);

  return (
    <div className="page-content">
      <div className="page-title-row">
        <div>
          <h2 className="page-title">Active Risk Alerts</h2>
          <div className="page-subtitle">Categorized real-time threat alerts requiring defensive merchant action</div>
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--accent-rose)', fontWeight: 600 }}>
          {activeSpikes.length} Active System Alerts
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {activeSpikes.map((spike) => (
          <div key={spike.merchant_id} className="section-card" style={{ borderLeft: '4px solid var(--accent-rose)', marginBottom: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <span className="badge-tier tier-critical">FRAUD SPIKE</span>
                  <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    Merchant: {spike.merchant_id}
                  </span>
                </div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.4rem' }}>
                  Reasons: <strong>{spike.spike_reasons.join(' | ')}</strong>
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--accent-rose)' }}>
                  {(spike.avg_risk_score * 100).toFixed(1)}% Avg Risk
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  High-Risk Txns: {spike.high_risk_txn_count} / {spike.window_txn_count} ({ (spike.high_risk_ratio * 100).toFixed(1) }%)
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1.5rem', marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)', fontSize: '0.82rem' }}>
              <div>
                <span style={{ color: 'var(--text-secondary)' }}>Window Volume:</span>
                <span style={{ fontWeight: 600, marginLeft: '0.3rem' }}>INR {spike.window_total_amount.toLocaleString()}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-secondary)' }}>Failure Rate:</span>
                <span style={{ fontWeight: 700, color: 'var(--accent-amber)', marginLeft: '0.3rem' }}>
                  {(spike.failed_rate * 100).toFixed(1)}%
                </span>
              </div>
              <div>
                <span style={{ color: 'var(--text-secondary)' }}>Recommended Action:</span>
                <span style={{ fontWeight: 700, color: 'var(--accent-blue)', marginLeft: '0.3rem' }}>
                  ENABLE 3DS STEP-UP & RATE-LIMIT CHECKOUT
                </span>
              </div>
            </div>
          </div>
        ))}

        {activeSpikes.length === 0 && (
          <div className="section-card" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
            <CheckCircle2 size={40} color="#10b981" style={{ margin: '0 auto 0.75rem' }} />
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              All Clear — No Active Fraud Spikes
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
              All 20 merchant accounts are operating within standard historical risk baselines.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
