import React, { useState, useEffect } from 'react';
import { History, ShieldCheck, FileText } from 'lucide-react';

export default function AuditLogView() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    async function fetchAudit() {
      try {
        const res = await fetch('/api/v1/risk/audit-log');
        if (res.ok) setLogs(await res.json());
      } catch (err) {
        console.error('Error fetching audit log:', err);
      }
    }
    fetchAudit();
  }, []);

  return (
    <div className="page-content">
      <div className="page-title-row">
        <div>
          <h2 className="page-title">Defensive System Audit Log</h2>
          <div className="page-subtitle">Production-grade audit trail of risk assessments, merchant spike alerts, and defensive actions</div>
        </div>
      </div>

      <div className="section-card" style={{ padding: '0.5rem' }}>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Event Type</th>
                <th>Entity / Subject ID</th>
                <th>System Decision & Action Taken</th>
                <th>Severity</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((event, idx) => (
                <tr key={idx}>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    {event.timestamp}
                  </td>
                  <td style={{ fontWeight: 700, fontSize: '0.8rem', color: 'var(--accent-blue)' }}>
                    {event.event_type}
                  </td>
                  <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{event.entity_id}</td>
                  <td>{event.system_decision}</td>
                  <td>
                    <span className={`badge-tier tier-${event.severity.toLowerCase()}`}>
                      {event.severity}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
