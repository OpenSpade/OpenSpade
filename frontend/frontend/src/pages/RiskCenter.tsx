import React, { useState } from 'react';
import { Download, Bell, AlertTriangle, TrendingUp, Clock, Calendar, Info } from 'lucide-react';

interface DelistingItem {
  pair: string;
  exchange: string;
  delistingDate: string;
  daysRemaining: string;
  currentPrice: string;
  change24h: string;
  riskLevel: 'high' | 'medium' | 'low';
  reason: string;
  status: string;
}

const delistingItems: DelistingItem[] = [
  {
    pair: 'LUNA2USDT',
    exchange: 'Binance',
    delistingDate: '2026-05-05',
    daysRemaining: '4天',
    currentPrice: '$0.45',
    change24h: '-12.3%',
    riskLevel: 'high',
    reason: '项目方申请退市',
    status: '待处理',
  },
  {
    pair: 'FTTUSDT',
    exchange: 'Binance',
    delistingDate: '2026-05-12',
    daysRemaining: '11天',
    currentPrice: '$1.23',
    change24h: '-8.5%',
    riskLevel: 'high',
    reason: '流动性不足',
    status: '待处理',
  },
  {
    pair: 'SRMUSDT',
    exchange: 'Binance',
    delistingDate: '2026-05-20',
    daysRemaining: '19天',
    currentPrice: '$0.12',
    change24h: '-3.2%',
    riskLevel: 'medium',
    reason: '合规要求',
    status: '监控中',
  },
  {
    pair: 'TOMOUSDT',
    exchange: 'Binance',
    delistingDate: '2026-05-30',
    daysRemaining: '29天',
    currentPrice: '$0.89',
    change24h: '+1.5%',
    riskLevel: 'medium',
    reason: '交易量低于标准',
    status: '监控中',
  },
];

const stats = [
  { label: '高风险交易对', value: '2', icon: AlertTriangle, color: 'bg-red-100 text-red-600' },
  { label: '即将下架', value: '2', icon: Clock, color: 'bg-yellow-100 text-yellow-600' },
  { label: '活跃风险事件', value: '1', icon: Calendar, color: 'bg-blue-100 text-blue-600' },
  { label: '今日预警', value: '4', icon: Bell, color: 'bg-purple-100 text-purple-600', extra: '1条紧急' },
];

export const RiskCenter: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'delisting' | 'events' | 'alerts'>('delisting');

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">风险中心</h2>
        <div className="flex items-center space-x-3">
          <button className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <Download className="w-5 h-5" />
            <span className="text-sm font-medium">风险报告</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
            <Bell className="w-5 h-5" />
            <span className="text-sm font-medium">预警设置</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
        {stats.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div key={idx} className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="text-sm text-gray-500 mb-1">{stat.label}</p>
                  <p className={`text-2xl font-bold ${stat.label.includes('高风险') ? 'text-red-600' : stat.label.includes('即将下架') ? 'text-yellow-600' : 'text-gray-800'}`}>
                    {stat.value}
                  </p>
                </div>
                <div className={`w-12 h-12 ${stat.color} rounded-lg flex items-center justify-center`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
              {stat.extra && (
                <p className="text-sm text-primary-600 font-medium">{stat.extra}</p>
              )}
            </div>
          );
        })}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="border-b border-gray-200">
          <div className="flex space-x-1 px-5">
            {[
              { id: 'delisting', label: '下架预警', icon: AlertTriangle },
              { id: 'events', label: '风险事件', icon: TrendingUp },
              { id: 'alerts', label: '实时预警', icon: Bell },
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

        <div className="p-6">
          {activeTab === 'delisting' && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-800">即将下架的交易对</h3>
                <div className="flex items-center space-x-1.5 text-sm text-gray-500">
                  <Info className="w-4 h-4" />
                  <span>建议及时处理相关持仓</span>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">交易对</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">交易所</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">下架日期</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">剩余天数</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">当前价格</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">24H涨跌</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">风险等级</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">原因</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    {delistingItems.map((item, idx) => (
                      <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-4 px-4">
                          <span className="text-sm font-semibold text-gray-800">{item.pair}</span>
                        </td>
                        <td className="py-4 px-4">
                          <span className="text-sm text-gray-600">{item.exchange}</span>
                        </td>
                        <td className="py-4 px-4">
                          <span className="text-sm text-gray-600">{item.delistingDate}</span>
                        </td>
                        <td className="py-4 px-4">
                          <span className={`text-sm font-semibold ${parseInt(item.daysRemaining) <= 7 ? 'text-red-600' : 'text-gray-700'}`}>
                            {item.daysRemaining}
                          </span>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <span className="text-sm text-gray-600">{item.currentPrice}</span>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <span className={`text-sm font-semibold ${item.change24h.startsWith('-') ? 'text-red-600' : 'text-green-600'}`}>
                            {item.change24h}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                            item.riskLevel === 'high' ? 'bg-red-100 text-red-700' :
                            item.riskLevel === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-green-100 text-green-700'
                          }`}>
                            {item.riskLevel === 'high' ? '高风险' :
                             item.riskLevel === 'medium' ? '中风险' : '低风险'}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <span className="text-sm text-gray-600">{item.reason}</span>
                        </td>
                        <td className="py-4 px-4">
                          <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                            item.status === '待处理' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {item.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'events' && (
            <div className="flex items-center justify-center h-48">
              <p className="text-gray-500">风险事件区域</p>
            </div>
          )}

          {activeTab === 'alerts' && (
            <div className="flex items-center justify-center h-48">
              <p className="text-gray-500">实时预警区域</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
