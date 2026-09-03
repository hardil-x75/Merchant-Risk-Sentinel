import React, { useState, useEffect } from 'react';
import { TrendingUp, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function MerchantSpikesView() {
  const [merchants, setMerchants] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchSpikes() {
      try {
        setLoading(true);
        const res = await fetch('/api/v1/risk/merchant-spikes');
        if (res.ok) setMerchants(await res.json());
      } catch (err) {
        console.error('Error fetching merchant spikes:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchSpikes();
  }, []);

  return (
    <div className="page-content">
      <div className="page-title-row">
        <div>
          <h2 className="page-title">Merchant Risk Spikes & Anomaly Monitor</h2>
          <div className="page-subtitle">
            Core Differentiator: Real-time merchant-level activity comparison vs historical baseline
          </div>
        </div>
      </div>

      {/* Merchant Risk Grid */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Merchant ID</th>
              <th>Current Risk Score</th>
              <th>Spike Status</th>
              <th>Current Activity vs Baseline</th>
              <th>High-Risk Ratio</th>
              <th>Failure Rate</th>
              <th>Defensive Recommendation</th>
            </tr>
          </thead>
          <tbody>
            {merchants.map((m) => {
              const isSpike = m.is_spike_alert;
              const currentVolume = m.window_total_amount;
              const normalBaselineVolume = m.window_avg_amount * 300; // Simulated baseline

              return (
                <tr key={m.merchant_id} style={{ backgroundColor: isSpike ? 'rgba(239, 68, 68, 0.05)' : 'transparent' }}>
                  <td style={{ fontWeight: 700, fontFamily: 'monospace' }}>{m.merchant_id}</td>
                  <td>
                    <span style={{ fontWeight: 800, color: isSpike ? 'var(--accent-rose)' : 'var(--accent-emerald)' }}>
                      {(m.avg_risk_score * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td>
                    {isSpike ? (
                      <span className="badge-tier tier-critical">FRAUD SPIKE</span>
                    ) : (
                      <span className="badge-tier tier-low">NORMAL</span>
                    )}
                  </td>
                  <td>
                    <div style={{ fontSize: '0.78rem' }}>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>INR {currentVolume.toLocaleString()}</span>
                      <span style={{ color: 'var(--text-muted)', marginLeft: '0.4rem' }}>
                        (Baseline: INR {normalBaselineVolume.toLocaleString()})
                      </span>
                    </div>
                  </td>
                  <td>
                    <span style={{ fontWeight: 600, color: m.high_risk_ratio > 0.1 ? 'var(--accent-amber)' : 'var(--text-primary)' }}>
                      {(m.high_risk_ratio * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td>
                    <span style={{ fontWeight: 600, color: m.failed_rate > 0.2 ? 'var(--accent-rose)' : 'var(--text-primary)' }}>
                      {(m.failed_rate * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td style={{ fontSize: '0.78rem', color: 'var(--accent-blue)', fontWeight: 600 }}>
                    {isSpike ? 'ENABLE 3DS STEP-UP' : 'MONITOR VELOCITY'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
