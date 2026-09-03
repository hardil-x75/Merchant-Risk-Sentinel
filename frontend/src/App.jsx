import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import LiveMonitorView from './components/LiveMonitorView';
import OverviewView from './components/OverviewView';
import TransactionsView from './components/TransactionsView';
import RiskAlertsView from './components/RiskAlertsView';
import MerchantSpikesView from './components/MerchantSpikesView';
import ModelPerformanceView from './components/ModelPerformanceView';
import AuditLogView from './components/AuditLogView';

export default function App() {
  const [activeTab, setActiveTab] = useState('monitor');
  const [selectedMerchant, setSelectedMerchant] = useState('ALL');
  const [selectedTxn, setSelectedTxn] = useState(null);
  const [demoStage, setDemoStage] = useState(1);

  // Guided 3-Stage Pitch Demo Logic
  const handleRunGuidedDemo = () => {
    // Stage 1: Normal traffic view
    setActiveTab('monitor');
    setSelectedMerchant('ALL');
    setSelectedTxn(null);
    setDemoStage(1);

    // Stage 2: Jump to Spike Anomaly
    setTimeout(() => {
      setSelectedMerchant('merch_03');
      setActiveTab('spikes');
      setDemoStage(2);
    }, 2500);

    // Stage 3: Investigate High-Risk Txn
    setTimeout(() => {
      setSelectedTxn({
        transaction_id: 'txn_004912',
        merchant_id: 'merch_03',
        customer_id: 'cust_0019',
        amount: 45000.0,
        currency: 'INR',
        payment_method: 'card',
        timestamp: '2026-09-02T21:10:00Z',
        transaction_status: 'captured',
        card_network: 'visa',
        bank_name: 'ICICI',
        email_domain: 'tempmail.com',
        billing_country: 'US',
        risk_score: 0.9450,
        risk_tier: 'CRITICAL',
        is_suspicious: true,
        decision: 'HOLD_FOR_REVIEW'
      });
      setDemoStage(3);
    }, 5500);
  };

  const handleResetDemo = () => {
    setActiveTab('monitor');
    setSelectedMerchant('ALL');
    setSelectedTxn(null);
    setDemoStage(1);
  };

  const handleJumpToPerformance = () => {
    setActiveTab('performance');
  };

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className="main-wrapper">
        <Header
          selectedMerchant={selectedMerchant}
          setSelectedMerchant={setSelectedMerchant}
          demoStage={demoStage}
          onRunGuidedDemo={handleRunGuidedDemo}
          onResetDemo={handleResetDemo}
          onJumpToPerformance={handleJumpToPerformance}
        />

        {activeTab === 'monitor' && (
          <LiveMonitorView onSelectTxn={setSelectedTxn} />
        )}

        {activeTab === 'overview' && (
          <OverviewView
            selectedMerchant={selectedMerchant}
            onSelectTxn={setSelectedTxn}
            onViewAllSpikes={() => setActiveTab('spikes')}
          />
        )}

        {activeTab === 'transactions' && (
          <TransactionsView
            selectedMerchant={selectedMerchant}
            selectedTxn={selectedTxn}
            setSelectedTxn={setSelectedTxn}
          />
        )}

        {activeTab === 'alerts' && (
          <RiskAlertsView onSelectTxn={setSelectedTxn} />
        )}

        {activeTab === 'spikes' && (
          <MerchantSpikesView />
        )}

        {activeTab === 'performance' && (
          <ModelPerformanceView />
        )}

        {activeTab === 'audit' && (
          <AuditLogView />
        )}
      </div>
    </div>
  );
}
