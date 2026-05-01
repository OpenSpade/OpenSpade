import React, { useState } from 'react';
import { Play, Save, Download, Calendar, TrendingUp, TrendingDown, Scale, ArrowDown } from 'lucide-react';

const statCards = [
  {
    title: '总收益率',
    value: '+0%',
    icon: TrendingUp,
    bgColor: 'bg-green-50',
    iconColor: 'text-green-500',
  },
  {
    title: '年化收益率',
    value: '0%',
    icon: Scale,
    bgColor: 'bg-blue-50',
    iconColor: 'text-blue-500',
  },
  {
    title: '夏普比率',
    value: '0',
    icon: Scale,
    bgColor: 'bg-yellow-50',
    iconColor: 'text-yellow-500',
  },
  {
    title: '最大回撤',
    value: '-0%',
    icon: ArrowDown,
    bgColor: 'bg-red-50',
    iconColor: 'text-red-500',
  },
];

export const Backtest: React.FC = () => {
  const [selectedStrategy, setSelectedStrategy] = useState('Grid Trading');
  const [startDate, setStartDate] = useState('2024/01/01');
  const [endDate, setEndDate] = useState('2024/06/30');
  const [initialCapital, setInitialCapital] = useState('100000');

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-800">回测分析</h2>
        <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
          <Play className="w-4 h-4" />
          <span className="text-sm">开始新回测</span>
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 p-5 mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">回测配置</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-gray-500 mb-2">选择策略</label>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option>Grid Trading</option>
              <option>DCA Strategy</option>
              <option>Trend Following</option>
              <option>Momentum Breakout</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-500 mb-2">开始日期</label>
            <div className="relative">
              <input
                type="text"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent pr-10"
              />
              <Calendar className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-500 mb-2">结束日期</label>
            <div className="relative">
              <input
                type="text"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent pr-10"
              />
              <Calendar className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-500 mb-2">初始资金</label>
            <input
              type="text"
              value={initialCapital}
              onChange={(e) => setInitialCapital(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="100000"
            />
          </div>
        </div>
        <div className="flex items-center space-x-3 mt-4">
          <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
            <Play className="w-4 h-4" />
            <span className="text-sm">运行回测</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors">
            <Save className="w-4 h-4" />
            <span className="text-sm">保存配置</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors opacity-50 cursor-not-allowed">
            <Download className="w-4 h-4" />
            <span className="text-sm">导出报告</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {statCards.map((card) => {
          const Icon = card.icon;
          const isPositive = !card.value.startsWith('-');
          return (
            <div key={card.title} className="bg-white rounded-xl p-5 border border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 mb-1">{card.title}</p>
                  <p className={`text-2xl font-bold ${isPositive ? 'text-success-500' : 'text-danger-500'}`}>
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
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">净值曲线</h3>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <span className="w-3 h-3 bg-primary-500 rounded-full"></span>
                <span className="text-sm text-gray-600">策略</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-3 h-3 bg-gray-400 rounded-full"></span>
                <span className="text-sm text-gray-600">基准</span>
              </div>
            </div>
          </div>
          <div className="h-72 flex items-center justify-center bg-gray-50 rounded-lg">
            <div className="text-center text-gray-400">
              <TrendingUp className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">运行回测后显示净值曲线</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">回撤分析</h3>
          <div className="h-72 flex items-center justify-center bg-gray-50 rounded-lg">
            <div className="text-center text-gray-400">
              <ArrowDown className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">运行回测后显示回撤分析</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
