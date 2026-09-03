import React from 'react';
import {
  Activity,
  LayoutDashboard,
  Receipt,
  ShieldAlert,
  TrendingUp,
  BrainCircuit,
  History
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'monitor', label: 'Live Risk Stream', icon: Activity },
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'transactions', label: 'Transactions', icon: Receipt },
    { id: 'alerts', label: 'Risk Alerts', icon: ShieldAlert },
    { id: 'spikes', label: 'Merchant Spikes', icon: TrendingUp },
    { id: 'performance', label: 'Model Performance', icon: BrainCircuit },
    { id: 'audit', label: 'Audit Log', icon: History },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <ShieldAlert size={22} color="#3b82f6" />
          <span className="sidebar-brand-title">Merchant Risk Sentinel</span>
        </div>
        <div className="sidebar-subtitle">Defensive AI Risk Manager</div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div>Razorpay Buildathon — Track 02</div>
        <div style={{ color: '#9ca3af', marginTop: '0.2rem' }}>Version 0.2.0 (Step 3)</div>
      </div>
    </aside>
  );
}
