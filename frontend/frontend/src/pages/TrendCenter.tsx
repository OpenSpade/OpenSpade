import React, { useState, useEffect } from 'react';
import { Download, RefreshCw, TrendingUp, TrendingDown, Activity, Clock, Zap, ArrowUpRight, ArrowDownRight, AlertCircle, Filter, Search } from 'lucide-react';

interface TrendItem {
  symbol: string;
  price: string;
  change24h: string;
  volume: string;
  trend: 'up' | 'down' | 'sideways';
  maStatus: string;
  signalStrength: 'strong' | 'medium' | 'weak';
  timeframe: string;
}

interface SignalData {
  id: number;
  batch_id: string;
  analysis_time: string;
  symbol: string;
  rank: number;
  composite_score: number;
  signal_strength: string;
  signal_strength_icon: string;
  volume_24h_usd: number;
  price_change_percent: number | null;
  vol_ratio_1d: number | null;
  vol_ratio_4h: number | null;
  vol_ratio_1h: number | null;
  score_1d: number | null;
  score_4h: number | null;
  score_1h: number | null;
  ma_status: string;
  recent_crossovers: string | null;
  timeframe_details: any;
  indicator_details: any;
}

const trendItems: TrendItem[] = [
  {
    symbol: 'BTCUSDT',
    price: '$67,523.45',
    change24h: '+3.25%',
    volume: '$2.4B',
    trend: 'up',
    maStatus: '7>25>100',
    signalStrength: 'strong',
    timeframe: '1D',
  },
  {
    symbol: 'ETHUSDT',
    price: '$3,421.89',
    change24h: '+5.67%',
    volume: '$1.8B',
    trend: 'up',
    maStatus: '7>25>100',
    signalStrength: 'strong',
    timeframe: '4H',
  },
  {
    symbol: 'SOLUSDT',
    price: '$178.56',
    change24h: '+8.34%',
    volume: '$890M',
    trend: 'up',
    maStatus: '100>7>25',
    signalStrength: 'medium',
    timeframe: '1H',
  },
  {
    symbol: 'AVAXUSDT',
    price: '$42.34',
    change24h: '-2.15%',
    volume: '$120M',
    trend: 'down',
    maStatus: '100>25>7',
    signalStrength: 'weak',
    timeframe: '1D',
  },
  {
    symbol: 'LINKUSDT',
    price: '$14.78',
    change24h: '+0.89%',
    volume: '$67M',
    trend: 'sideways',
    maStatus: '7>25',
    signalStrength: 'medium',
    timeframe: '4H',
  },
  {
    symbol: 'DOTUSDT',
    price: '$7.23',
    change24h: '+4.56%',
    volume: '$234M',
    trend: 'up',
    maStatus: '7>25>100',
    signalStrength: 'strong',
    timeframe: '1H',
  },
];

const stats = [
  { label: '上涨趋势', value: '128', icon: TrendingUp, color: 'bg-green-100 text-green-600', change: '+12' },
  { label: '下跌趋势', value: '89', icon: TrendingDown, color: 'bg-red-100 text-red-600', change: '-5' },
  { label: '横盘整理', value: '67', icon: Activity, color: 'bg-gray-100 text-gray-600', change: '+3' },
  { label: '突破信号', value: '23', icon: Zap, color: 'bg-yellow-100 text-yellow-600', change: '+8' },
];

const API_BASE_URL = 'http://localhost:8080/api/v1';

export const TrendCenter: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'trending' | 'signals' | 'analysis'>('trending');
  const [timeframe, setTimeframe] = useState('1D');
  const [signalData, setSignalData] = useState<SignalData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStrength, setFilterStrength] = useState<string>('all');

  useEffect(() => {
    if (activeTab === 'signals') {
      fetchSignals();
    }
  }, [activeTab]);

  const fetchSignals = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/trend/signals?limit=50`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      if (result.success) {
        setSignalData(result.data);
      } else {
        setError('获取数据失败');
      }
    } catch (err) {
      setError('无法连接到服务器');
      console.error('Error fetching signals:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    if (activeTab === 'signals') {
      fetchSignals();
    }
  };

  const filteredSignals = signalData.filter(item => {
    const matchesSearch = item.symbol.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStrength = filterStrength === 'all' || item.signal_strength.toLowerCase() === filterStrength.toLowerCase();
    return matchesSearch && matchesStrength;
  });

  const formatVolume = (volume: number): string => {
    if (volume >= 1e9) {
      return `$${(volume / 1e9).toFixed(2)}B`;
    } else if (volume >= 1e6) {
      return `$${(volume / 1e6).toFixed(2)}M`;
    } else if (volume >= 1e3) {
      return `$${(volume / 1e3).toFixed(2)}K`;
    }
    return `$${volume.toFixed(2)}`;
  };

  const getStrengthColor = (strength: string): string => {
    switch (strength.toLowerCase()) {
      case 'strong':
        return 'bg-red-100 text-red-700';
      case 'medium':
        return 'bg-yellow-100 text-yellow-700';
      case 'weak':
        return 'bg-green-100 text-green-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getStrengthLabel = (strength: string): string => {
    switch (strength.toLowerCase()) {
      case 'strong':
        return '强信号';
      case 'medium':
        return '中信号';
      case 'weak':
        return '弱信号';
      default:
        return strength;
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">趋势中心</h2>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1 bg-white rounded-lg border border-gray-200 p-1">
            {['1H', '4H', '1D', '1W'].map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  timeframe === tf
                    ? 'bg-primary-100 text-primary-600'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
          <button 
            onClick={handleRefresh}
            className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            <span className="text-sm font-medium">刷新</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
            <Download className="w-5 h-5" />
            <span className="text-sm font-medium">导出报告</span>
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
              <p className={`text-sm font-medium ${stat.change.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>
                {stat.change}
              </p>
            </div>
          );
        })}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="border-b border-gray-200">
          <div className="flex space-x-1 px-5">
            {[
              { id: 'trending', label: '实时趋势', icon: TrendingUp },
              { id: 'signals', label: '突破信号', icon: Zap },
              { id: 'analysis', label: '趋势分析', icon: Activity },
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
          {activeTab === 'trending' && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-800">当前趋势监控</h3>
                <div className="flex items-center space-x-1.5 text-sm text-gray-500">
                  <Clock className="w-4 h-4" />
                  <span>实时更新</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {trendItems.map((item, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-xl border ${
                      item.trend === 'up' ? 'border-green-200 bg-green-50/30' :
                      item.trend === 'down' ? 'border-red-200 bg-red-50/30' :
                      'border-gray-200 bg-gray-50/30'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <p className="text-lg font-bold text-gray-800">{item.symbol}</p>
                        <p className="text-sm text-gray-500">周期: {item.timeframe}</p>
                      </div>
                      {item.trend === 'up' ? (
                        <ArrowUpRight className="w-6 h-6 text-green-600" />
                      ) : item.trend === 'down' ? (
                        <ArrowDownRight className="w-6 h-6 text-red-600" />
                      ) : (
                        <Activity className="w-6 h-6 text-gray-500" />
                      )}
                    </div>
                    
                    <div className="flex items-end justify-between">
                      <div>
                        <p className="text-xl font-bold text-gray-800">{item.price}</p>
                        <p className={`text-sm font-semibold ${
                          item.change24h.startsWith('+') ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {item.change24h}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-500">成交量</p>
                        <p className="text-sm font-medium text-gray-700">{item.volume}</p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-200/50">
                      <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700 font-medium">
                        {item.maStatus}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                        item.signalStrength === 'strong' ? 'bg-yellow-100 text-yellow-700' :
                        item.signalStrength === 'medium' ? 'bg-blue-100 text-blue-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {item.signalStrength === 'strong' ? '强信号' :
                         item.signalStrength === 'medium' ? '中信号' : '弱信号'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'signals' && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-4">
                  <h3 className="text-lg font-semibold text-gray-800">突破信号</h3>
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <Clock className="w-4 h-4" />
                    <span>实时更新</span>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="搜索交易对..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                  <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
                    {['all', 'strong', 'medium', 'weak'].map((strength) => (
                      <button
                        key={strength}
                        onClick={() => setFilterStrength(strength)}
                        className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                          filterStrength === strength
                            ? 'bg-white text-gray-800 shadow-sm'
                            : 'text-gray-500 hover:text-gray-700'
                        }`}
                      >
                        {strength === 'all' ? '全部' : getStrengthLabel(strength)}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {loading ? (
                <div className="flex items-center justify-center h-48">
                  <div className="flex items-center space-x-2">
                    <RefreshCw className="w-5 h-5 animate-spin text-primary-600" />
                    <span className="text-gray-500">加载中...</span>
                  </div>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center h-48">
                  <div className="flex items-center space-x-2 text-red-500">
                    <AlertCircle className="w-5 h-5" />
                    <span>{error}</span>
                  </div>
                </div>
              ) : filteredSignals.length === 0 ? (
                <div className="flex items-center justify-center h-48">
                  <p className="text-gray-500">暂无突破信号数据</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">排名</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">交易对</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">综合评分</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">信号强度</th>
                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-600">24h成交额</th>
                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-600">涨跌幅</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">均线状态</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">量比</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">突破情况</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredSignals.map((signal) => (
                        <tr key={signal.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                          <td className="py-3 px-4">
                            <span className="inline-flex items-center justify-center w-6 h-6 bg-primary-100 text-primary-600 rounded-full text-xs font-bold">
                              {signal.rank}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span className="font-medium text-gray-800">{signal.symbol}</span>
                          </td>
                          <td className="py-3 px-4">
                            <span className={`text-sm font-semibold ${
                              signal.composite_score >= 0.7 ? 'text-red-600' :
                              signal.composite_score >= 0.4 ? 'text-yellow-600' :
                              'text-gray-600'
                            }`}>
                              {signal.composite_score.toFixed(3)}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getStrengthColor(signal.signal_strength)}`}>
                              <span>{signal.signal_strength_icon}</span>
                              <span>{getStrengthLabel(signal.signal_strength)}</span>
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right">
                            <span className="text-gray-700">{formatVolume(signal.volume_24h_usd)}</span>
                          </td>
                          <td className="py-3 px-4 text-right">
                            <span className={`font-medium ${
                              signal.price_change_percent !== null && signal.price_change_percent >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {signal.price_change_percent !== null ? `${signal.price_change_percent >= 0 ? '+' : ''}${signal.price_change_percent.toFixed(2)}%` : '-'}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                              {signal.ma_status}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex space-x-2 text-xs">
                              {signal.vol_ratio_1d !== null && (
                                <span className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">
                                  1D: {signal.vol_ratio_1d.toFixed(2)}
                                </span>
                              )}
                              {signal.vol_ratio_4h !== null && (
                                <span className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">
                                  4H: {signal.vol_ratio_4h.toFixed(2)}
                                </span>
                              )}
                              {signal.vol_ratio_1h !== null && (
                                <span className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">
                                  1H: {signal.vol_ratio_1h.toFixed(2)}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            <span className="text-xs text-gray-500">
                              {signal.recent_crossovers || '暂无'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
                    <span>共 {filteredSignals.length} 条记录</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'analysis' && (
            <div className="flex items-center justify-center h-48">
              <p className="text-gray-500">趋势分析区域</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};