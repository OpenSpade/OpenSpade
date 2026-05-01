import React, { useState } from 'react';
import { Upload, Plus, Play, Edit2, Copy, Trash2, Pause } from 'lucide-react';

const mockStrategies = [
  {
    id: 1,
    name: 'Grid Trading - BTCUSDT',
    type: 'grid',
    profit: '+¥10,868.74',
    profitRate: '+22.94%',
    trades: 101,
    winRate: '59.7%',
    maxDrawdown: '11.4%',
    status: 'running',
    startTime: '2026-03-03 19:29',
  },
  {
    id: 2,
    name: 'DCA Strategy - ETHUSDT',
    type: 'dca',
    profit: '+¥7,181.11',
    profitRate: '+10.04%',
    trades: 168,
    winRate: '66.4%',
    maxDrawdown: '5.7%',
    status: 'running',
    startTime: '2026-03-03 19:29',
  },
  {
    id: 3,
    name: 'Trend Following - SOLUSDT',
    type: 'trend',
    profit: '+¥15,913.04',
    profitRate: '+21.39%',
    trades: 94,
    winRate: '58.6%',
    maxDrawdown: '6.6%',
    status: 'running',
    startTime: '2026-04-20 19:29',
  },
];

const stoppedStrategies = [
  {
    id: 4,
    name: 'Momentum Breakout - ADAUSDT',
    type: 'momentum',
    profit: '+¥2,345.67',
    profitRate: '+5.23%',
    trades: 45,
    winRate: '62.1%',
    maxDrawdown: '8.9%',
    status: 'stopped',
    startTime: '2026-02-15 10:30',
  },
  {
    id: 5,
    name: 'RSI Reversal - DOTUSDT',
    type: 'reversal',
    profit: '-¥1,234.56',
    profitRate: '-3.12%',
    trades: 78,
    winRate: '45.2%',
    maxDrawdown: '15.3%',
    status: 'stopped',
    startTime: '2026-01-20 14:45',
  },
];

const templateStrategies = [
  { id: 1, name: '网格交易模板', type: 'grid', description: '经典网格交易策略' },
  { id: 2, name: 'DCA定投模板', type: 'dca', description: '美元成本平均策略' },
  { id: 3, name: '趋势跟踪模板', type: 'trend', description: '均线交叉趋势策略' },
  { id: 4, name: '动量突破模板', type: 'momentum', description: '突破交易策略' },
  { id: 5, name: '均值回归模板', type: 'reversal', description: '反转交易策略' },
];

type TabType = 'running' | 'stopped' | 'template';

export const Strategy: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('running');

  const tabs = [
    { id: 'running' as TabType, label: '运行中', count: 3 },
    { id: 'stopped' as TabType, label: '已停止', count: 2 },
    { id: 'template' as TabType, label: '策略模板', count: 5 },
  ];

  const strategies = activeTab === 'running' ? mockStrategies : activeTab === 'stopped' ? stoppedStrategies : templateStrategies;

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-800">策略管理</h2>
        <div className="flex items-center space-x-3">
          <button className="flex items-center space-x-2 px-4 py-2 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors">
            <Upload className="w-4 h-4" />
            <span className="text-sm">导入策略</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
            <Plus className="w-4 h-4" />
            <span className="text-sm">创建策略</span>
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-100">
        <div className="flex border-b border-gray-100">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 text-sm font-medium transition-colors relative ${
                activeTab === tab.id
                  ? 'text-primary-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
              <span className="ml-2 px-2 py-0.5 bg-gray-100 rounded-full text-xs">
                {tab.count}
              </span>
              {activeTab === tab.id && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600"></span>
              )}
            </button>
          ))}
        </div>

        <div className="p-4">
          {activeTab !== 'template' ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">策略信息</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">类型</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">盈亏</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">收益率</th>
                    <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">交易次数</th>
                    <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">胜率</th>
                    <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">最大回撤</th>
                    <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">状态</th>
                    <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {(strategies as typeof mockStrategies).map((strategy) => (
                    <tr key={strategy.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-4 px-4">
                        <p className="text-sm font-medium text-gray-800">{strategy.name}</p>
                        <p className="text-xs text-gray-500 mt-1">启动时间: {strategy.startTime}</p>
                      </td>
                      <td className="py-4 px-4">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                          strategy.type === 'grid' ? 'bg-blue-100 text-blue-600' :
                          strategy.type === 'dca' ? 'bg-green-100 text-green-600' :
                          strategy.type === 'trend' ? 'bg-purple-100 text-purple-600' :
                          'bg-gray-100 text-gray-600'
                        }`}>
                          {strategy.type}
                        </span>
                      </td>
                      <td className={`py-4 px-4 text-right text-sm font-medium ${
                        strategy.profit.startsWith('+') ? 'text-success-500' : 'text-danger-500'
                      }`}>
                        {strategy.profit}
                      </td>
                      <td className={`py-4 px-4 text-right text-sm font-medium ${
                        strategy.profitRate.startsWith('+') ? 'text-success-500' : 'text-danger-500'
                      }`}>
                        {strategy.profitRate}
                      </td>
                      <td className="py-4 px-4 text-center text-sm text-gray-600">{strategy.trades}</td>
                      <td className="py-4 px-4 text-center text-sm text-gray-600">{strategy.winRate}</td>
                      <td className={`py-4 px-4 text-center text-sm font-medium ${
                        parseFloat(strategy.maxDrawdown) > 10 ? 'text-danger-500' : 'text-gray-600'
                      }`}>
                        {strategy.maxDrawdown}
                      </td>
                      <td className="py-4 px-4 text-center">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                          strategy.status === 'running' ? 'bg-success-100 text-success-600' : 'bg-gray-100 text-gray-600'
                        }`}>
                          {strategy.status === 'running' ? '运行中' : '已停止'}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center justify-center space-x-2">
                          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors" title="启动">
                            <Play className="w-4 h-4 text-success-500" />
                          </button>
                          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors" title="编辑">
                            <Edit2 className="w-4 h-4 text-gray-600" />
                          </button>
                          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors" title="复制">
                            <Copy className="w-4 h-4 text-gray-600" />
                          </button>
                          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors" title="删除">
                            <Trash2 className="w-4 h-4 text-danger-500" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {(strategies as typeof templateStrategies).map((template) => (
                <div key={template.id} className="p-4 border border-gray-100 rounded-lg hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-800">{template.name}</p>
                      <p className="text-xs text-gray-500 mt-1">{template.description}</p>
                    </div>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                      template.type === 'grid' ? 'bg-blue-100 text-blue-600' :
                      template.type === 'dca' ? 'bg-green-100 text-green-600' :
                      template.type === 'trend' ? 'bg-purple-100 text-purple-600' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {template.type}
                    </span>
                  </div>
                  <div className="flex items-center justify-end space-x-2 mt-4">
                    <button className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50">
                      预览
                    </button>
                    <button className="px-3 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                      使用模板
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
