import React from 'react';
import { X, ShieldAlert, CheckCircle, AlertTriangle, Lock } from 'lucide-react';

export default function TransactionDetailModal({ txn, onClose }) {
  if (!txn) return null;

  const isHighRisk = txn.is_suspicious;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>
              Transaction Inspection Drawer
            </div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'monospace', color: 'var(--text-primary)', marginTop: '0.2rem' }}>
              {txn.transaction_id}
            </div>
          </div>
          <button className="btn-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* AI Risk Score Banner */}
        <div
          style={{
            background: isHighRisk ? 'rgba(239, 68, 68, 0.12)' : 'rgba(16, 185, 129, 0.12)',
            border: `1px solid ${isHighRisk ? '#ef4444' : '#10b981'}`,
            borderRadius: '8px',
            padding: '1.25rem',
            marginBottom: '1.5rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div>
            <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', fontWeight: 700, color: isHighRisk ? 'var(--accent-rose)' : 'var(--accent-emerald)' }}>
              Sentinel Risk Assessment
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '0.1rem' }}>
              {(txn.risk_score * 100).toFixed(1)}% <span style={{ fontSize: '1.2rem', fontWeight: 600 }}>{txn.risk_tier} RISK</span>
            </div>
          </div>

          <span className={`badge-tier tier-${txn.risk_tier.toLowerCase()}`} style={{ fontSize: '0.85rem', padding: '0.4rem 0.8rem' }}>
            {txn.risk_tier}
          </span>
        </div>

        {/* Transaction Summary */}
        <div className="section-card" style={{ marginBottom: '1.25rem', padding: '1rem' }}>
          <div className="section-header" style={{ marginBottom: '0.75rem', fontSize: '0.9rem' }}>
            <span>Payment Attributes</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.82rem' }}>
            <div>
              <span style={{ color: 'var(--text-secondary)' }}>Merchant ID:</span>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{txn.merchant_id}</div>
            </div>

            <div>
              <span style={{ color: 'var(--text-secondary)' }}>Customer ID:</span>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{txn.customer_id}</div>
            </div>

            <div>
              <span style={{ color: 'var(--text-secondary)' }}>Amount:</span>
              <div style={{ fontWeight: 700, color: 'var(--accent-blue)' }}>INR {txn.amount.toLocaleString()}</div>
            </div>

            <div>
              <span style={{ color: 'var(--text-secondary)' }}>Payment Method:</span>
              <div style={{ fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-primary)' }}>{txn.payment_method}</div>
            </div>

            <div>
              <span style={{ color: 'var(--text-secondary)' }}>Timestamp:</span>
              <div style={{ color: 'var(--text-primary)' }}>{new Date(txn.timestamp).toLocaleString()}</div>
            </div>

            <div>
              <span style={{ color: 'var(--text-secondary)' }}>Email Domain:</span>
              <div style={{ color: 'var(--text-primary)' }}>{txn.email_domain || 'N/A'}</div>
            </div>
          </div>
        </div>

        {/* Why Was This Flagged? (Deterministic Reason Codes) */}
        <div className="section-card" style={{ marginBottom: '1.25rem', padding: '1rem' }}>
          <div className="section-header" style={{ marginBottom: '0.75rem', fontSize: '0.9rem' }}>
            <span>Why was this flagged? (Deterministic Signal Attribution)</span>
          </div>

          {isHighRisk ? (
            <div>
              <div className="reason-box" style={{ borderLeftColor: 'var(--accent-rose)' }}>
                <div className="reason-title">Elevated 1-Hour Transaction Velocity</div>
                <div className="reason-desc">Customer attempted 8 transactions in past 60 minutes (Baseline threshold: 4.0).</div>
              </div>

              <div className="reason-box" style={{ borderLeftColor: 'var(--accent-amber)' }}>
                <div className="reason-title">Amount Ratio Above Merchant Baseline</div>
                <div className="reason-desc">Transaction amount is 4.5x higher than merchant's 30-day average order value.</div>
              </div>

              <div className="reason-box" style={{ borderLeftColor: 'var(--accent-amber)' }}>
                <div className="reason-title">Burst of Failed Attempts</div>
                <div className="reason-desc">Customer recorded 4 declined transactions in 30 minutes prior to this attempt.</div>
              </div>
            </div>
          ) : (
            <div className="reason-box" style={{ borderLeftColor: 'var(--accent-emerald)' }}>
              <div className="reason-title">Normal Baseline Traffic</div>
              <div className="reason-desc">All sliding window velocity, amount ratio, and retry metrics are within standard operating bounds.</div>
            </div>
          )}
        </div>

        {/* Defensive Action Panel */}
        <div className="section-card" style={{ padding: '1rem', background: '#0b0f19' }}>
          <div className="section-header" style={{ marginBottom: '0.75rem', fontSize: '0.9rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <ShieldAlert color="#3b82f6" size={16} />
              <span>Recommended Defensive Controls</span>
            </div>
          </div>

          <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 600, marginBottom: '0.5rem' }}>
            System Recommendation: <span style={{ color: 'var(--accent-blue)', textTransform: 'uppercase' }}>{txn.decision}</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.75rem' }}>
            <button className="btn-demo btn-demo-primary" style={{ width: '100%', textAlign: 'center', padding: '0.6rem' }}>
              Execute {txn.decision} Safeguard
            </button>
            <button className="btn-demo" style={{ width: '100%', textAlign: 'center', padding: '0.6rem' }}>
              Log Merchant Audit Event
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
