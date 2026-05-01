import React, { useState } from 'react';
import { Download, Plus, ShieldAlert, TrendingDown, TrendingUp, Gauge, AlertTriangle, Gavel, Settings, Activity } from 'lucide-react';

export const Risk: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'limits' | 'alerts' | 'settings'>('overview');

  const stats = [
    { label: '组合VaR (95%)', value: '¥12,193', icon: AlertTriangle, color: 'bg-yellow-100 text-yellow-600', isWarning: true },
    { label: '最大回撤', value: '-5.3%', icon: TrendingDown, color: 'bg-red-100 text-red-600', isNegative: true },
    { label: 'Beta系数', value: '0.83', icon: TrendingUp, color: 'bg-blue-100 text-blue-600' },
    { label: '活跃预警', value: '0', icon: AlertTriangle, color: 'bg-yellow-100 text-yellow-600' },
  ];

  const sectors = [
    { name: 'Layer 1', exposure: '49%', limit: '50%', color: '#F59E0B' },
    { name: 'DeFi', exposure: '18.5%', limit: '30%', color: '#3B82F6' },
    { name: 'Layer 2', exposure: '5.2%', limit: '20%', color: '#3B82F6' },
    { name: 'Meme', exposure: '6.2%', limit: '10%', color: '#3B82F6' },
    { name: 'GameFi', exposure: '1.1%', limit: '15%', color: '#3B82F6' },
  ];

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">风险管理</h2>
        <div className="flex items-center space-x-3">
          <button className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <Download className="w-5 h-5" />
            <span className="text-sm font-medium">风险报告</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
            <Plus className="w-5 h-5" />
            <span className="text-sm font-medium">新增规则</span>
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
                  <p className={`text-2xl font-bold ${
                    stat.isNegative ? 'text-red-600' : 
                    stat.isWarning ? 'text-yellow-600' : 
                    'text-gray-800'
                  }`}>
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

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="border-b border-gray-200">
          <div className="flex space-x-1 px-5">
            {[
              { id: 'overview', label: '风险概览', icon: ShieldAlert },
              { id: 'limits', label: '风险限额', icon: Gavel },
              { id: 'alerts', label: '风险预警', icon: AlertTriangle },
              { id: 'settings', label: '风控设置', icon: Settings },
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
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">风险指标趋势</h3>
                <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
                  <div className="text-center">
                    <Activity className="w-12 h-12 mx-auto text-gray-400 mb-2" />
                    <p className="text-gray-500">图表区域</p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">行业风险敞口</h3>
                <div className="space-y-4">
                  {sectors.map((sector, idx) => {
                    const exposurePercent = parseInt(sector.exposure);
                    const limitPercent = parseInt(sector.limit);
                    const width = (exposurePercent / limitPercent) * 100;
                    return (
                      <div key={idx}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-700">{sector.name}</span>
                          <span className="text-sm text-gray-600">{sector.exposure} / {sector.limit}</span>
                        </div>
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full rounded-full transition-all duration-300"
                            style={{ width: `${Math.min(width, 100)}%`, backgroundColor: sector.color }}
                          ></div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'limits' && (
            <div className="flex items-center justify-center h-48">
              <p className="text-gray-500">风险限额设置区域</p>
            </div>
          )}
          
          {activeTab === 'alerts' && (
            <div className="flex items-center justify-center h-48">
              <p className="text-gray-500">风险预警区域</p>
            </div>
          )}
          
          {activeTab === 'settings' && (
            <div className="flex items-center justify-center h-48">
              <p className="text-gray-500">风控设置区域</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
