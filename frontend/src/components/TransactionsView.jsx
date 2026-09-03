import React, { useState, useEffect } from 'react';
import { Search, Filter, RefreshCw } from 'lucide-react';
import TransactionDetailModal from './TransactionDetailModal';

export default function TransactionsView({ selectedMerchant, selectedTxn, setSelectedTxn }) {
  const [transactions, setTransactions] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [search, setSearch] = useState('');
  const [tierFilter, setTierFilter] = useState('ALL');
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const limit = 25;

  useEffect(() => {
    async function fetchTxns() {
      try {
        setLoading(true);
        let url = `/api/v1/risk/transactions?merchant_id=${selectedMerchant}&limit=${limit}&offset=${offset}`;
        if (tierFilter !== 'ALL') url += `&risk_tier=${tierFilter}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;

        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          setTransactions(data.transactions || []);
          setTotalCount(data.total_count || 0);
        }
      } catch (err) {
        console.error('Error fetching transactions:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchTxns();
  }, [selectedMerchant, tierFilter, search, offset]);

  return (
    <div className="page-content">
      <div className="page-title-row">
        <div>
          <h2 className="page-title">Transaction Risk Explorer</h2>
          <div className="page-subtitle">Search, filter, and inspect scored transactions with deterministic reason codes</div>
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Showing {transactions.length} of {totalCount} records
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="filter-bar">
        <input
          type="text"
          className="search-input"
          placeholder="Search by Transaction ID, Customer ID, Merchant, Payment Method..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setOffset(0); }}
        />

        <select
          className="merchant-select"
          value={tierFilter}
          onChange={(e) => { setTierFilter(e.target.value); setOffset(0); }}
        >
          <option value="ALL">All Risk Tiers</option>
          <option value="LOW">LOW Risk</option>
          <option value="MEDIUM">MEDIUM Risk</option>
          <option value="HIGH">HIGH Risk</option>
          <option value="CRITICAL">CRITICAL Risk</option>
        </select>
      </div>

      {/* Transaction Table */}
      <div className="section-card" style={{ padding: '0.5rem' }}>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Transaction ID</th>
                <th>Merchant</th>
                <th>Customer</th>
                <th>Amount</th>
                <th>Method</th>
                <th>Timestamp</th>
                <th>Risk Score</th>
                <th>Tier</th>
                <th>Defensive Action</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((txn) => (
                <tr key={txn.transaction_id} onClick={() => setSelectedTxn(txn)}>
                  <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{txn.transaction_id}</td>
                  <td>{txn.merchant_id}</td>
                  <td>{txn.customer_id}</td>
                  <td style={{ fontWeight: 700 }}>INR {txn.amount.toLocaleString()}</td>
                  <td style={{ textTransform: 'uppercase', fontSize: '0.78rem' }}>{txn.payment_method}</td>
                  <td style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    {new Date(txn.timestamp).toLocaleString()}
                  </td>
                  <td style={{ fontWeight: 800, color: txn.is_suspicious ? 'var(--accent-rose)' : 'var(--accent-emerald)' }}>
                    {(txn.risk_score * 100).toFixed(1)}%
                  </td>
                  <td>
                    <span className={`badge-tier tier-${txn.risk_tier.toLowerCase()}`}>
                      {txn.risk_tier}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--accent-blue)' }}>
                    {txn.decision}
                  </td>
                </tr>
              ))}

              {transactions.length === 0 && !loading && (
                <tr>
                  <td colSpan="9" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No transactions found matching criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
        <button
          className="btn-demo"
          disabled={offset === 0}
          onClick={() => setOffset(Math.max(0, offset - limit))}
        >
          Previous
        </button>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Page {Math.floor(offset / limit) + 1} of {Math.ceil(totalCount / limit) || 1}
        </span>
        <button
          className="btn-demo"
          disabled={offset + limit >= totalCount}
          onClick={() => setOffset(offset + limit)}
        >
          Next
        </button>
      </div>

      {/* Transaction Detail Drawer Modal */}
      {selectedTxn && (
        <TransactionDetailModal txn={selectedTxn} onClose={() => setSelectedTxn(null)} />
      )}
    </div>
  );
}
