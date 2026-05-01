import React from 'react';
import { Plus, Share2, Eye, Flame, Calendar, RefreshCw } from 'lucide-react';

const stats = [
  { label: '总分享数', value: '0', icon: Share2, color: 'bg-blue-100 text-blue-600' },
  { label: '总浏览量', value: '0', icon: Eye, color: 'bg-green-100 text-green-600' },
  { label: '最热分享', value: '0', icon: Flame, color: 'bg-orange-100 text-orange-600' },
  { label: '本月分享', value: '0', icon: Calendar, color: 'bg-purple-100 text-purple-600' },
];

export const Share: React.FC = () => {
  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">分享中心</h2>
        <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
          <Plus className="w-5 h-5" />
          <span className="text-sm font-medium">创建分享</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
        {stats.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div key={idx} className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 mb-1">{stat.label}</p>
                  <p className="text-2xl font-bold text-gray-800">{stat.value}</p>
                </div>
                <div className={`w-12 h-12 ${stat.color} rounded-lg flex items-center justify-center`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-800">分享历史</h3>
          <button className="flex items-center space-x-1.5 text-sm text-primary-600 hover:text-primary-700 transition-colors">
            <RefreshCw className="w-4 h-4" />
            <span>刷新</span>
          </button>
        </div>

        <div className="flex flex-col items-center justify-center py-12">
          <Share2 className="w-12 h-12 text-gray-400 mb-4" />
          <p className="text-gray-600">暂无分享记录，创建你的第一个分享吧！</p>
        </div>
      </div>
    </div>
  );
};
