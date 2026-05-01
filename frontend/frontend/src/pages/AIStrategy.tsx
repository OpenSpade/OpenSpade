import React, { useState } from 'react';
import { FileCode, Play, TrendingUp, Clock, Wand2, BookOpen } from 'lucide-react';

const strategyTypes = [
  {
    id: 'trend',
    name: '趋势跟踪策略',
    description: '基于移动平均线交叉和趋势强度指标，自动识别市场趋势并顺势交易',
    metrics: { profit: '15-30%', risk: '中等', period: '4h-1d' },
    selected: true,
  },
  {
    id: 'mean-reversion',
    name: '均值回归策略',
    description: '利用布林带和RSI指标识别超买超卖，在价格偏离均值时进行反向交易',
    metrics: { profit: '10-25%', risk: '中低', period: '1h-4h' },
    selected: false,
  },
  {
    id: 'momentum',
    name: '动量突破策略',
    description: '捕捉价格突破关键阻力位的瞬间，配合成交量确认进行快速交易',
    metrics: { profit: '20-45%', risk: '较高', period: '15m-1h' },
    selected: false,
  },
];

const statCards = [
  { title: '已生成策略', value: '', icon: FileCode, bgColor: 'bg-blue-50', iconColor: 'text-blue-500' },
  { title: '运行中策略', value: '1', icon: Play, bgColor: 'bg-green-50', iconColor: 'text-green-500' },
  { title: '平均收益率', value: '14.9%', icon: TrendingUp, bgColor: 'bg-yellow-50', iconColor: 'text-yellow-500' },
  { title: '平均生成时间', value: '分', icon: Clock, bgColor: 'bg-purple-50', iconColor: 'text-purple-500' },
];

type TabType = 'create' | 'generated' | 'templates';

export const AIStrategy: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('create');
  const [selectedStrategy, setSelectedStrategy] = useState(strategyTypes[0]);
  const [strategyDescription, setStrategyDescription] = useState('');

  const tabs = [
    { id: 'create' as TabType, label: '创建策略', icon: Wand2 },
    { id: 'generated' as TabType, label: '已生成策略', icon: FileCode },
    { id: 'templates' as TabType, label: '策略模板', icon: BookOpen },
  ];

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-800">AI写策略</h2>
        <div className="flex items-center space-x-3">
          <button className="flex items-center space-x-2 px-4 py-2 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors">
            <BookOpen className="w-4 h-4" />
            <span className="text-sm">策略文档</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
            <Wand2 className="w-4 h-4" />
            <span className="text-sm">AI助手</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.title} className="bg-white rounded-xl p-5 border border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 mb-1">{card.title}</p>
                  <p className="text-2xl font-bold text-gray-800">{card.value}</p>
                </div>
                <div className={`w-12 h-12 ${card.bgColor} rounded-lg flex items-center justify-center`}>
                  <Icon className={`w-6 h-6 ${card.iconColor}`} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-white rounded-xl border border-gray-100">
        <div className="flex border-b border-gray-100">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-6 py-3 text-sm font-medium transition-colors relative ${
                  activeTab === tab.id
                    ? 'text-primary-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
                {activeTab === tab.id && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600"></span>
                )}
              </button>
            );
          })}
        </div>

        <div className="p-6">
          {activeTab === 'create' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">AI策略生成器</h3>
                <p className="text-sm text-gray-500 mb-4">选择策略类型</p>
                
                <div className="space-y-3">
                  {strategyTypes.map((strategy) => (
                    <div
                      key={strategy.id}
                      onClick={() => setSelectedStrategy(strategy)}
                      className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                        selectedStrategy.id === strategy.id
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-100 hover:border-gray-200'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-gray-800">{strategy.name}</span>
                        {selectedStrategy.id === strategy.id && (
                          <span className="w-5 h-5 bg-primary-500 rounded-full flex items-center justify-center">
                            <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                            </svg>
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 mb-3">{strategy.description}</p>
                      <div className="flex items-center space-x-4">
                        <span className="text-xs">
                          <span className="text-gray-400">收益:</span>{' '}
                          <span className="text-success-600 font-medium">{strategy.metrics.profit}</span>
                        </span>
                        <span className="text-xs">
                          <span className="text-gray-400">风险:</span>{' '}
                          <span className="font-medium">{strategy.metrics.risk}</span>
                        </span>
                        <span className="text-xs">
                          <span className="text-gray-400">周期:</span>{' '}
                          <span className="font-medium">{strategy.metrics.period}</span>
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-6">
                  <label className="block text-sm text-gray-500 mb-2">策略描述</label>
                  <textarea
                    value={strategyDescription}
                    onChange={(e) => setStrategyDescription(e.target.value)}
                    className="w-full p-3 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    rows={4}
                    placeholder="描述你想要的策略特点..."
                  />
                </div>

                <button className="mt-6 w-full py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium">
                  生成AI策略
                </button>
              </div>

              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-800">生成的策略代码</h3>
                  <button className="flex items-center space-x-1 text-sm text-primary-600 hover:text-primary-700">
                    <Wand2 className="w-4 h-4" />
                    <span>AI驱动</span>
                  </button>
                </div>
                <div className="h-96 bg-gray-900 rounded-lg p-4 overflow-auto">
                  <div className="flex items-center justify-center h-full text-gray-400">
                    <div className="text-center">
                      <FileCode className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p className="text-sm">点击"生成AI策略"开始创建</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'generated' && (
            <div className="text-center py-12">
              <FileCode className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">暂无已生成的策略</p>
            </div>
          )}

          {activeTab === 'templates' && (
            <div className="text-center py-12">
              <BookOpen className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">暂无策略模板</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
