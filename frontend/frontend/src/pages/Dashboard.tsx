import React from 'react';
import { TrendingUp, TrendingDown, Briefcase, Target, ChevronRight, Activity } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

const mockProfitData = [
  { date: '04/01', value: 5000 },
  { date: '04/03', value: 8000 },
  { date: '04/05', value: -5000 },
  { date: '04/07', value: 15000 },
  { date: '04/10', value: 32000 },
  { date: '04/13', value: 28000 },
  { date: '04/15', value: 35000 },
  { date: '04/17', value: 38000 },
  { date: '04/20', value: 30000 },
  { date: '04/22', value: 45000 },
  { date: '04/25', value: 65000 },
  { date: '04/27', value: 78000 },
  { date: '04/30', value: 90000 },
];

const mockPortfolioData = [
  { symbol: 'BTCUSDT', amount: 82604.12, change: 6.66 },
  { symbol: 'ETHUSDT', amount: 119499.53, change: -1.93 },
  { symbol: 'BNBUSDT', amount: 111635.07, change: -4.37 },
  { symbol: 'SOLUSDT', amount: 113020.27, change: 2.06 },
  { symbol: 'XRPUSDT', amount: 184235.55, change: 5.14 },
];

const statCards = [
  {
    title: '总资产',
    value: '¥891,291.53',
    subValue: '¥891,291.53',
    change: '+4.8%',
    changeLabel: '较昨日',
    isPositive: true,
    icon: Briefcase,
    bgColor: 'bg-blue-50',
    iconColor: 'text-blue-500',
  },
  {
    title: '今日盈亏',
    value: '+¥42,785.45',
    subValue: '+¥42,785.45',
    change: '+4.8%',
    changeLabel: '收益率',
    isPositive: true,
    icon: TrendingUp,
    bgColor: 'bg-green-50',
    iconColor: 'text-green-500',
  },
  {
    title: '活跃策略',
    value: '4',
    subValue: '4',
    change: '39',
    changeLabel: '今日交易',
    isPositive: true,
    icon: Activity,
    bgColor: 'bg-yellow-50',
    iconColor: 'text-yellow-500',
  },
  {
    title: '胜率',
    value: '59.7%',
    subValue: '59.7%',
    change: '+3.2%',
    changeLabel: '较上周',
    isPositive: true,
    icon: Target,
    bgColor: 'bg-purple-50',
    iconColor: 'text-purple-500',
  },
];

export const Dashboard: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.title} className="bg-white rounded-xl p-5 border border-gray-100 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500 mb-1">{card.title}</p>
                  <p className="text-2xl font-bold text-gray-800">{card.value}</p>
                  <p className="text-lg font-semibold text-gray-600 mt-1">{card.subValue}</p>
                  <div className={`flex items-center space-x-1 mt-2 ${card.isPositive ? 'text-success-500' : 'text-danger-500'}`}>
                    {card.isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                    <span className="text-sm font-medium">{card.change}</span>
                    <span className="text-xs text-gray-400">{card.changeLabel}</span>
                  </div>
                </div>
                <div className={`w-12 h-12 ${card.bgColor} rounded-lg flex items-center justify-center`}>
                  <Icon className={`w-6 h-6 ${card.iconColor}`} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-100 p-5">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-800">收益曲线</h3>
            <div className="flex items-center space-x-2">
              {['7天', '30天', '90天'].map((period) => (
                <button
                  key={period}
                  className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                    period === '30天'
                      ? 'bg-primary-500 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  {period}
                </button>
              ))}
            </div>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={mockProfitData}>
                <defs>
                  <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#9ca3af', fontSize: 12 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#9ca3af', fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    padding: '12px',
                  }}
                  formatter={(value: number) => [`¥${value.toLocaleString()}`, '收益']}
                />
                <Area type="monotone" dataKey="value" stroke="#3b82f6" fill="url(#colorGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">持仓分布</h3>
            <button className="text-sm text-primary-600 hover:text-primary-700 flex items-center space-x-1">
              <span>查看全部</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
          <div className="space-y-4">
            {mockPortfolioData.map((item) => (
              <div key={item.symbol} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
                    <span className="text-xs font-bold text-primary-600">{item.symbol.slice(0, 2)}</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-800">{item.symbol}</p>
                    <p className="text-xs text-gray-500">¥{item.amount.toLocaleString()}</p>
                  </div>
                </div>
                <span className={`text-sm font-medium ${item.change >= 0 ? 'text-success-500' : 'text-danger-500'}`}>
                  {item.change >= 0 ? '+' : ''}{item.change}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 p-5">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">策略监控</h3>
        <div className="border-t border-gray-100">
        </div>
      </div>
    </div>
  );
};
