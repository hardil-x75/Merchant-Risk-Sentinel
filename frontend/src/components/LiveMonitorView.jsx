import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, AlertTriangle, ShieldAlert, Zap, CheckCircle2 } from 'lucide-react';

export default function LiveMonitorView({ onSelectTxn }) {
  const [stream, setStream] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [mode, setMode] = useState('NORMAL');
  const [latestHighRisk, setLatestHighRisk] = useState(null);
  const timerRef = useRef(null);

  useEffect(() => {
    async function fetchStream() {
      try {
        const res = await fetch(`/api/v1/risk/simulation-stream?mode=${mode}&limit=30`);
        if (res.ok) {
          const data = await res.json();
          setStream(data);
          setCurrentIndex(0);
        }
      } catch (err) {
        console.error('Error fetching simulation stream:', err);
      }
    }
    fetchStream();
  }, [mode]);

  useEffect(() => {
    if (isPlaying && stream.length > 0) {
      timerRef.current = setInterval(() => {
        setCurrentIndex((prev) => {
          const next = prev + 1;
          if (next >= stream.length) {
            setIsPlaying(false);
            return prev;
          }
          const item = stream[next];
          if (item && item.is_suspicious) {
            setLatestHighRisk(item);
          }
          return next;
        });
      }, 1200);
    } else {
      clearInterval(timerRef.current);
    }

    return () => clearInterval(timerRef.current);
  }, [isPlaying, stream]);

  const handleStart = () => setIsPlaying(true);
  const handlePause = () => setIsPlaying(false);
  const handleReset = () => {
    setIsPlaying(false);
    setCurrentIndex(0);
    setLatestHighRisk(null);
  };

  const visibleTransactions = stream.slice(0, currentIndex + 1);
  const currentItem = stream[currentIndex];

  return (
    <div className="page-content">
      <div className="page-title-row">
        <div>
          <h2 className="page-title">Live Risk Stream Monitor</h2>
          <div className="page-subtitle">Real-time sequential transaction playback using actual synthetic benchmark records</div>
        </div>
        <div className="status-pill">
          <span className="status-dot" style={{ backgroundColor: isPlaying ? '#10b981' : '#f59e0b' }}></span>
          <span>{isPlaying ? 'STREAMING ACTIVE' : 'STREAM PAUSED'}</span>
        </div>
      </div>

      {/* Control Toolbar */}
      <div className="section-card" style={{ padding: '1rem', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {!isPlaying ? (
              <button className="btn-demo btn-demo-primary" onClick={handleStart}>
                <Play size={14} style={{ marginRight: '0.3rem', display: 'inline' }} /> Start Stream
              </button>
            ) : (
              <button className="btn-demo" onClick={handlePause}>
                <Pause size={14} style={{ marginRight: '0.3rem', display: 'inline' }} /> Pause
              </button>
            )}

            <button className="btn-demo" onClick={handleReset}>
              <RotateCcw size={14} style={{ marginRight: '0.3rem', display: 'inline' }} /> Reset
            </button>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600 }}>SCENARIO:</span>
            <button
              className={`btn-demo ${mode === 'NORMAL' ? 'btn-demo-primary' : ''}`}
              onClick={() => { setMode('NORMAL'); handleReset(); }}
            >
              Normal Traffic
            </button>
            <button
              className={`btn-demo ${mode === 'SPIKE' ? 'btn-demo-primary' : ''}`}
              onClick={() => { setMode('SPIKE'); handleReset(); }}
            >
              Simulate Spike (merch_03)
            </button>
            <button
              className={`btn-demo ${mode === 'HIGH_RISK' ? 'btn-demo-primary' : ''}`}
              onClick={() => { setMode('HIGH_RISK'); handleReset(); }}
            >
              High-Risk Stream
            </button>
          </div>
        </div>
      </div>

      {/* Latest High-Risk Alert Card */}
      {latestHighRisk && (
        <div
          className="section-card"
          style={{
            borderLeft: '4px solid var(--accent-rose)',
            background: 'rgba(239, 68, 68, 0.08)',
            marginBottom: '1.5rem',
            animation: 'pulse-border 2s infinite'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <ShieldAlert color="#ef4444" size={20} />
                <span style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--accent-rose)' }}>
                  HIGH-RISK TRANSACTION DETECTED IN STREAM
                </span>
                <span className="badge-tier tier-critical">{latestHighRisk.risk_tier}</span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: '0.4rem' }}>
                Txn ID: <strong style={{ fontFamily: 'monospace' }}>{latestHighRisk.transaction_id}</strong> | Merchant: <strong>{latestHighRisk.merchant_id}</strong> | Amount: <strong>INR {latestHighRisk.amount.toLocaleString()}</strong>
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-rose)' }}>
                {(latestHighRisk.risk_score * 100).toFixed(1)}% Score
              </div>
              <button
                className="btn-demo btn-demo-primary"
                style={{ marginTop: '0.4rem' }}
                onClick={() => onSelectTxn(latestHighRisk)}
              >
                Inspect Reason & Mitigate
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Streamed Transactions Table */}
      <div className="section-card">
        <div className="section-header">
          <span>Live Ingested Transactions ({visibleTransactions.length} / {stream.length})</span>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Txn ID</th>
                <th>Merchant</th>
                <th>Customer</th>
                <th>Amount</th>
                <th>Method</th>
                <th>Risk Score</th>
                <th>Risk Tier</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {visibleTransactions.slice().reverse().map((item) => (
                <tr
                  key={item.transaction_id}
                  onClick={() => onSelectTxn(item)}
                  style={{
                    backgroundColor: item.is_suspicious ? 'rgba(239, 68, 68, 0.08)' : 'transparent'
                  }}
                >
                  <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{item.transaction_id}</td>
                  <td>{item.merchant_id}</td>
                  <td>{item.customer_id}</td>
                  <td style={{ fontWeight: 700 }}>INR {item.amount.toLocaleString()}</td>
                  <td style={{ textTransform: 'uppercase', fontSize: '0.78rem' }}>{item.payment_method}</td>
                  <td style={{ fontWeight: 800, color: item.is_suspicious ? 'var(--accent-rose)' : 'var(--accent-emerald)' }}>
                    {(item.risk_score * 100).toFixed(1)}%
                  </td>
                  <td>
                    <span className={`badge-tier tier-${item.risk_tier.toLowerCase()}`}>
                      {item.risk_tier}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.78rem', color: 'var(--accent-blue)', fontWeight: 600 }}>
                    {item.decision}
                  </td>
                </tr>
              ))}

              {visibleTransactions.length === 0 && (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    Click "Start Stream" or select a scenario above to begin live transaction playback.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
