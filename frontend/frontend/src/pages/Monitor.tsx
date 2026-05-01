import React from 'react';
import { Plus, Play, Radio, RefreshCw, Eye, ChevronRight } from 'lucide-react';

const mockContentSources = [
  {
    id: 1,
    name: 'CoinDesk News',
    type: 'RSS',
    lastCheck: '2026/4/30 09:53:08',
    status: 'active',
  },
  {
    id: 2,
    name: 'CryptoBanter',
    type: 'YouTube',
    lastCheck: '2026/4/30 09:08:08',
    status: 'active',
  },
];

const mockGeneratedStrategies = [
  {
    id: 1,
    name: '基于YouTube分析的趋势策略',
    description: '从Cryptobanter频道分析提取的BTC趋势交易策略',
    status: 'backtested',
    tags: ['已回测', 'AI生成'],
    metrics: { totalReturn: '1850.00%', sharpe: '1.85', maxDrawdown: '720.00%', winRate: '6500.0%' },
    createdAt: '2026/4/29 19:30:21',
  },
  {
    id: 2,
    name: '基于RSS新闻的事件驱动策略',
    description: '从CoinDesk新闻中提取的事件驱动交易信号',
    status: 'created',
    tags: ['已创建', 'AI生成'],
    metrics: { totalReturn: '1230.00%', sharpe: '1.42', maxDrawdown: '910.00%', winRate: '5800.0%' },
    createdAt: '2026/5/1 14:30:21',
  },
];

const statCards = [
  {
    title: '监听状态',
    value: '已停止',
    status: 'stopped',
    icon: Radio,
    bgColor: 'bg-red-50',
    iconColor: 'text-red-500',
  },
  {
    title: '内容源数量',
    value: '2',
    status: 'active',
    icon: Radio,
    bgColor: 'bg-blue-50',
    iconColor: 'text-blue-500',
  },
  {
    title: '生成策略',
    value: '2',
    status: 'active',
    icon: Play,
    bgColor: 'bg-yellow-50',
    iconColor: 'text-yellow-500',
  },
];

export const Monitor: React.FC = () => {
  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-800">内容监听中心</h2>
        <div className="flex items-center space-x-3">
          <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
            <Plus className="w-4 h-4" />
            <span className="text-sm">添加内容源</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 bg-success-600 text-white rounded-lg hover:bg-success-700 transition-colors">
            <Play className="w-4 h-4" />
            <span className="text-sm">开始监听</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.title} className="bg-white rounded-xl p-5 border border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 mb-1">{card.title}</p>
                  <p className={`text-2xl font-bold ${card.status === 'stopped' ? 'text-danger-500' : 'text-gray-800'}`}>
                    {card.value}
                  </p>
                </div>
                <div className={`w-12 h-12 ${card.bgColor} rounded-lg flex items-center justify-center`}>
                  <Icon className={`w-6 h-6 ${card.iconColor}`} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-100">
          <div className="p-4 border-b border-gray-100">
            <h3 className="text-lg font-semibold text-gray-800">内容源</h3>
          </div>
          <div className="divide-y divide-gray-50">
            {mockContentSources.map((source) => (
              <div key={source.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
                <div className="flex items-center space-x-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    source.type === 'RSS' ? 'bg-orange-100' : 'bg-red-100'
                  }`}>
                    <Radio className={`w-5 h-5 ${
                      source.type === 'RSS' ? 'text-orange-500' : 'text-red-500'
                    }`} />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-800">{source.name}</p>
                    <p className="text-xs text-gray-500">最后检查: {source.lastCheck}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                    source.type === 'RSS' ? 'bg-orange-100 text-orange-600' : 'bg-red-100 text-red-600'
                  }`}>
                    {source.type}
                  </span>
                  <span className="px-2.5 py-1 bg-success-100 text-success-600 rounded-full text-xs font-medium">
                    活跃
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-100">
          <div className="p-4 border-b border-gray-100 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800">自动生成的策略</h3>
            <button className="flex items-center space-x-1 text-sm text-primary-600 hover:text-primary-700">
              <RefreshCw className="w-4 h-4" />
              <span>刷新</span>
            </button>
          </div>
          <div className="p-4 space-y-4">
            {mockGeneratedStrategies.map((strategy) => (
              <div key={strategy.id} className="p-4 border border-gray-100 rounded-lg">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="text-sm font-medium text-gray-800">{strategy.name}</p>
                    <p className="text-xs text-gray-500 mt-1">{strategy.description}</p>
                  </div>
                  <div className="flex items-center space-x-1">
                    {strategy.tags.map((tag) => (
                      <span key={tag} className={`px-2 py-0.5 rounded text-xs font-medium ${
                        tag === '已回测' ? 'bg-blue-100 text-blue-600' : 'bg-purple-100 text-purple-600'
                      }`}>
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-2 mb-3">
                  <div>
                    <p className="text-xs text-gray-400">总收益</p>
                    <p className="text-sm font-medium text-success-500">{strategy.metrics.totalReturn}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">夏普比率</p>
                    <p className="text-sm font-medium text-gray-800">{strategy.metrics.sharpe}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">最大回撤</p>
                    <p className="text-sm font-medium text-danger-500">{strategy.metrics.maxDrawdown}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">胜率</p>
                    <p className="text-sm font-medium text-success-500">{strategy.metrics.winRate}</p>
                  </div>
                </div>
                <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                  <span className="text-xs text-gray-400">{strategy.createdAt}</span>
                  <div className="flex items-center space-x-2">
                    <button className="flex items-center space-x-1 px-3 py-1.5 text-sm border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50">
                      <Eye className="w-4 h-4" />
                      <span>查看</span>
                    </button>
                    <button className="flex items-center space-x-1 px-3 py-1.5 text-sm bg-success-600 text-white rounded-lg hover:bg-success-700">
                      <Play className="w-4 h-4" />
                      <span>启动</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
