import React, { useState } from 'react';
import { Download, Bell, Coins, ArrowRightLeft, Percent, TrendingUp, Clock, ArrowUpRight } from 'lucide-react';

export const Fee: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'funding' | 'trading' | 'analysis'>('funding');

  const stats = [
    { label: '今日总费用', value: '¥956.5', icon: Coins, color: 'bg-red-100 text-red-600', change: '+15.2%', changePositive: false },
    { label: '交易手续费', value: '¥679.12', icon: ArrowRightLeft, color: 'bg-blue-100 text-blue-600', share: '71.2%' },
    { label: '资金费用', value: '¥277.38', icon: Percent, color: 'bg-yellow-100 text-yellow-600', share: '28.8%' },
    { label: '平均费率', value: '0.057%', icon: TrendingUp, color: 'bg-green-100 text-green-600', change: '-0.008%', changePositive: true },
  ];

  const rates = [
    { pair: 'BTCUSDT', current: '-2.3900%', predicted: '12.9400%', avg7d: '5.2700%', trend: 'up', next: '00:30' },
    { pair: 'ETHUSDT', current: '-0.3400%', predicted: '13.7000%', avg7d: '6.6800%', trend: 'up', next: '20:30' },
    { pair: 'BNBUSDT', current: '-4.9000%', predicted: '5.0200%', avg7d: '0.0600%', trend: 'up', next: '00:30' },
    { pair: 'SOLUSDT', current: '10.6000%', predicted: '11.9900%', avg7d: '11.2900%', trend: 'up', next: '02:30' },
    { pair: 'XRPUSDT', current: '0.0400%', predicted: '4.5700%', avg7d: '2.3000%', trend: 'up', next: '23:30' },
    { pair: 'ADAUSDT', current: '-3.1000%', predicted: '3.2100%', avg7d: '0.0500%', trend: 'up', next: '22:30' },
    { pair: 'DOGEUSDT', current: '-1.5200%', predicted: '11.3900%', avg7d: '4.9300%', trend: 'up', next: '22:30' },
  ];

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">费率中心</h2>
        <div className="flex items-center space-x-3">
          <button className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <Download className="w-5 h-5" />
            <span className="text-sm font-medium">导出报告</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
            <Bell className="w-5 h-5" />
            <span className="text-sm font-medium">费率提醒</span>
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
                  <p className="text-2xl font-bold text-gray-800">{stat.value}</p>
                </div>
                <div className={`w-12 h-12 ${stat.color} rounded-lg flex items-center justify-center`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
              {stat.change && (
                <p className={`text-sm font-medium ${stat.changePositive ? 'text-green-600' : 'text-red-600'}`}>
                  {stat.change}
                  <span className="text-gray-500 ml-2 font-normal">较昨日</span>
                </p>
              )}
              {stat.share && (
                <p className="text-sm text-gray-600">
                  {stat.share}
                  <span className="text-gray-500 ml-2">占比</span>
                </p>
              )}
            </div>
          );
        })}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="border-b border-gray-200">
          <div className="flex space-x-1 px-5">
            {[
              { id: 'funding', label: '资金费率', icon: Percent },
              { id: 'trading', label: '交易手续费', icon: ArrowRightLeft },
              { id: 'analysis', label: '费用分析', icon: TrendingUp },
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
          {activeTab === 'funding' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-800">实时资金费率</h3>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <Clock className="w-4 h-4" />
                  <span>下次结算: 2024-04-29 08:00:00</span>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">交易对</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">当前费率</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">预测费率</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">7日均值</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">趋势</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">下次结算</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rates.map((rate, idx) => (
                      <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-4 px-4">
                          <span className="text-sm font-medium text-gray-800">{rate.pair}</span>
                        </td>
                        <td className={`text-right py-4 px-4 text-sm font-medium ${
                          parseFloat(rate.current) < 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {rate.current}
                        </td>
                        <td className="text-right py-4 px-4 text-sm font-medium text-red-600">
                          {rate.predicted}
                        </td>
                        <td className="text-right py-4 px-4 text-sm font-medium text-red-600">
                          {rate.avg7d}
                        </td>
                        <td className="text-right py-4 px-4">
                          <span className="flex items-center justify-end space-x-1 text-sm font-medium text-red-600">
                            <ArrowUpRight className="w-3 h-3" />
                            <span>{rate.trend === 'up' ? '上升' : '下降'}</span>
                          </span>
                        </td>
                        <td className="text-right py-4 px-4 text-sm text-gray-700">
                          {rate.next}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          
          {activeTab === 'trading' && (
            <div className="flex items-center justify-center h-48">
              <p className="text-gray-500">交易手续费区域</p>
            </div>
          )}
          
          {activeTab === 'analysis' && (
            <div className="flex items-center justify-center h-48">
              <p className="text-gray-500">费用分析区域</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
