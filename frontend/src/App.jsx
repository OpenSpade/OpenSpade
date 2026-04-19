import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [portfolio, setPortfolio] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // 模拟获取资产数据
  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        // 模拟API请求延迟
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // 模拟数据，实际项目中应该从API获取
        const mockData = {
          total_assets: 15000.50,
          available_balance: 5000.25,
          locked_funds: 10000.25,
          allocation_ratio: 0.67,
          active_positions: [
            {
              symbol: "BTCUSDT",
              amount: 0.05,
              entry_price: 40000.00,
              current_value: 2000.00,
              unrealized_pnl: 100.00,
              leverage: 5,
              margin_type: "cross"
            },
            {
              symbol: "ETHUSDT",
              amount: 1.0,
              entry_price: 2000.00,
              current_value: 2000.00,
              unrealized_pnl: -50.00,
              leverage: 3,
              margin_type: "cross"
            }
          ],
          strategies: [
            {
              strategy_id: "grid_1",
              type: "grid",
              symbol: "BTCUSDT",
              state: "active",
              initial_amount: 5000.00,
              current_amount: 5050.00,
              occupied_amount: 4800.00,
              grid_num: 10,
              price_range: "38000.00 - 42000.00",
              current_price: 40100.00,
              grid_count: 5,
              profit_count: 3
            },
            {
              strategy_id: "dca_1",
              type: "dca",
              symbol: "ETHUSDT",
              state: "active",
              initial_amount: 3000.00,
              current_amount: 2900.00,
              occupied_amount: 3200.00,
              trigger_price: 2100.00,
              trigger_reason: "grid_broken",
              total_invested: 500.00,
              total_shares: 0.25,
              average_cost: 2000.00,
              dca_count: 2,
              last_dca_time: "2024-01-01T12:00:00"
            }
          ],
          timestamp: new Date().toISOString()
        }
        
        setPortfolio(mockData)
        setLoading(false)
      } catch (err) {
        setError('Failed to fetch portfolio data')
        setLoading(false)
      }
    }

    fetchPortfolioData()
  }, [])

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading portfolio data...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container">
        <div className="error">{error}</div>
      </div>
    )
  }

  return (
    <div className="container">
      <header className="header">
        <h1>OpenSpade - Portfolio Dashboard</h1>
        <p className="timestamp">Last updated: {new Date(portfolio.timestamp).toLocaleString()}</p>
      </header>

      <section className="summary-cards">
        <div className="card">
          <h3>Total Assets</h3>
          <p className="value">${portfolio.total_assets.toFixed(2)}</p>
        </div>
        <div className="card">
          <h3>Available Balance</h3>
          <p className="value">${portfolio.available_balance.toFixed(2)}</p>
        </div>
        <div className="card">
          <h3>Locked Funds</h3>
          <p className="value">${portfolio.locked_funds.toFixed(2)}</p>
        </div>
        <div className="card">
          <h3>Allocation Ratio</h3>
          <p className="value">{Math.round(portfolio.allocation_ratio * 100)}%</p>
        </div>
      </section>

      <section className="positions-section">
        <h2>Active Positions</h2>
        {portfolio.active_positions.length > 0 ? (
          <div className="positions-table">
            <div className="table-header">
              <div>Symbol</div>
              <div>Amount</div>
              <div>Entry Price</div>
              <div>Current Value</div>
              <div>Unrealized PnL</div>
              <div>Leverage</div>
            </div>
            {portfolio.active_positions.map((position, index) => (
              <div key={index} className="table-row">
                <div>{position.symbol}</div>
                <div>{position.amount}</div>
                <div>${position.entry_price.toFixed(2)}</div>
                <div>${position.current_value.toFixed(2)}</div>
                <div className={position.unrealized_pnl >= 0 ? 'positive' : 'negative'}>
                  {position.unrealized_pnl >= 0 ? '+' : ''}{position.unrealized_pnl.toFixed(2)}
                </div>
                <div>x{position.leverage}</div>
              </div>
            ))}
          </div>
        ) : (
          <p className="no-data">No active positions</p>
        )}
      </section>

      <section className="strategies-section">
        <h2>Trading Strategies</h2>
        {portfolio.strategies.length > 0 ? (
          <div className="strategies-grid">
            {portfolio.strategies.map((strategy) => (
              <div key={strategy.strategy_id} className="strategy-card">
                <div className="strategy-header">
                  <h3>{strategy.symbol} - {strategy.type.toUpperCase()}</h3>
                  <span className={`status ${strategy.state}`}>{strategy.state}</span>
                </div>
                <div className="strategy-details">
                  <div className="detail-item">
                    <span className="label">Initial Amount:</span>
                    <span className="value">${strategy.initial_amount.toFixed(2)}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Current Amount:</span>
                    <span className="value">${strategy.current_amount.toFixed(2)}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Occupied Amount:</span>
                    <span className="value">${strategy.occupied_amount.toFixed(2)}</span>
                  </div>
                  {strategy.type === 'grid' && (
                    <>
                      <div className="detail-item">
                        <span className="label">Grid Count:</span>
                        <span className="value">{strategy.grid_count}</span>
                      </div>
                      <div className="detail-item">
                        <span className="label">Profit Count:</span>
                        <span className="value">{strategy.profit_count}</span>
                      </div>
                      <div className="detail-item">
                        <span className="label">Price Range:</span>
                        <span className="value">{strategy.price_range}</span>
                      </div>
                    </>
                  )}
                  {strategy.type === 'dca' && (
                    <>
                      <div className="detail-item">
                        <span className="label">Total Invested:</span>
                        <span className="value">${strategy.total_invested.toFixed(2)}</span>
                      </div>
                      <div className="detail-item">
                        <span className="label">DCA Count:</span>
                        <span className="value">{strategy.dca_count}</span>
                      </div>
                      <div className="detail-item">
                        <span className="label">Average Cost:</span>
                        <span className="value">${strategy.average_cost.toFixed(2)}</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="no-data">No active strategies</p>
        )}
      </section>
    </div>
  )
}

export default App
