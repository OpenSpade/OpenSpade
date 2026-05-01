import React, { useState } from 'react';
import { Download, Plus, Wallet, TrendingUp, Layers, Coins, Briefcase, TrendingDown, ArrowUpRight } from 'lucide-react';

export const Portfolio: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'holdings' | 'trades' | 'performance'>('holdings');

  const stats = [
    { label: '总市值', value: '¥852,166.59', icon: Wallet, color: 'bg-blue-100 text-blue-600' },
    { label: '浮动盈亏', value: '+¥42,785.45', icon: TrendingUp, color: 'bg-green-100 text-green-600', isPositive: true },
    { label: '持仓数量', value: '9', icon: Layers, color: 'bg-yellow-100 text-yellow-600' },
    { label: '现金余额', value: '¥84,919.88', icon: Coins, color: 'bg-gray-100 text-gray-600' },
  ];

  const assets = [
    { name: 'BTC', percentage: 42.4, color: '#F7931A' },
    { name: 'ETH', percentage: 37.0, color: '#627EEA' },
    { name: 'BNB', percentage: 10.1, color: '#F3BA2F' },
    { name: 'SOL', percentage: 6.0, color: '#00FFA3' },
    { name: 'Others', percentage: 4.5, color: '#9CA3AF' },
  ];

  const holdings = [
    { symbol: 'BTC', quantity: '0.42', avgPrice: '45,200', currentPrice: '51,300', pnl: '+13.5%', value: '¥149,874' },
    { symbol: 'ETH', quantity: '5.2', avgPrice: '1,680', currentPrice: '1,850', pnl: '+10.1%', value: '¥68,420' },
    { symbol: 'BNB', quantity: '25', avgPrice: '280', currentPrice: '315', pnl: '+12.5%', value: '¥56,250' },
  ];

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">投资组合</h2>
        <div className="flex items-center space-x-3">
          <button className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <Download className="w-5 h-5" />
            <span className="text-sm font-medium">导出报告</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
            <Plus className="w-5 h-5" />
            <span className="text-sm font-medium">手动交易</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
        {stats.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div key={idx} className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 mb-1">{stat.label}</p>
                  <p className={`text-2xl font-bold ${stat.isPositive ? 'text-green-600' : 'text-gray-800'}`}>
                    {stat.value}
                  </p>
                </div>
                <div className={`w-12 h-12 ${stat.color} rounded-lg flex items-center justify-center`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-1 bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">资产配置</h3>
          <div className="relative flex items-center justify-center mb-6">
            <svg viewBox="0 0 100 100" className="w-48 h-48 transform -rotate-90">
              {(() => {
                let currentAngle = 0;
                return assets.map((asset, idx) => {
                  const angle = (asset.percentage / 100) * 360;
                  const startAngle = currentAngle;
                  currentAngle += angle;
                  
                  const startRad = (startAngle * Math.PI) / 180;
                  const endRad = (currentAngle * Math.PI) / 180;
                  
                  const x1 = 50 + 35 * Math.cos(startRad);
                  const y1 = 50 + 35 * Math.sin(startRad);
                  const x2 = 50 + 35 * Math.cos(endRad);
                  const y2 = 50 + 35 * Math.sin(endRad);
                  
                  const largeArc = angle > 180 ? 1 : 0;
                  
                  return (
                    <path
                      key={idx}
                      d={`M 50 50 L ${x1} ${y1} A 35 35 0 ${largeArc} 1 ${x2} ${y2} Z`}
                      fill={asset.color}
                      stroke="white"
                      strokeWidth="2"
                    />
                  );
                });
              })()}
              <circle cx="50" cy="50" r="22" fill="white" />
            </svg>
          </div>
          <div className="space-y-2">
            {assets.map((asset, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: asset.color }}></div>
                  <span className="text-sm text-gray-700">{asset.name}</span>
                </div>
                <span className="text-sm font-medium text-gray-800">{asset.percentage}%</span>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">组合表现</h3>
          <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
            <p className="text-gray-500">图表区域</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="border-b border-gray-200">
          <div className="flex space-x-1 px-5">
            {[
              { id: 'holdings', label: '持仓明细', icon: Briefcase },
              { id: 'trades', label: '交易记录', icon: TrendingDown },
              { id: 'performance', label: '业绩分析', icon: TrendingUp },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 px-4 py-3 text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'text-primary-600 border-b-2 border-primary-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="p-5">
          {activeTab === 'holdings' && (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">币种</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">数量</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">均价</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">现价</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">盈亏</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">市值</th>
                  </tr>
                </thead>
                <tbody>
                  {holdings.map((holding, idx) => (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-4 px-4">
                        <span className="text-sm font-medium text-gray-800">{holding.symbol}</span>
                      </td>
                      <td className="text-right py-4 px-4 text-sm text-gray-700">{holding.quantity}</td>
                      <td className="text-right py-4 px-4 text-sm text-gray-700">${holding.avgPrice}</td>
                      <td className="text-right py-4 px-4 text-sm text-gray-700">${holding.currentPrice}</td>
                      <td className="text-right py-4 px-4 text-sm font-medium text-green-600">
                        <span className="flex items-center justify-end space-x-1">
                          <ArrowUpRight className="w-3 h-3" />
                          <span>{holding.pnl}</span>
                        </span>
                      </td>
                      <td className="text-right py-4 px-4 text-sm font-medium text-gray-800">{holding.value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
          {activeTab === 'trades' && (
            <div className="flex items-center justify-center h-48">
              <p className="text-gray-500">交易记录区域</p>
            </div>
          )}
          
          {activeTab === 'performance' && (
            <div className="flex items-center justify-center h-48">
              <p className="text-gray-500">业绩分析区域</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
