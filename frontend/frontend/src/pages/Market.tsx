import React, { useState } from 'react';
import { Plus, FileText, Users, Calendar, Tag, Heart, MessageCircle, Eye, Clock } from 'lucide-react';

interface Post {
  id: number;
  author: string;
  type: string;
  time: string;
  title: string;
  content: string;
  tags: string[];
  likes: number;
  comments: number;
  views: number;
}

const posts: Post[] = [
  {
    id: 1,
    author: 'CryptoTrader',
    type: '交易心得',
    time: '1天前',
    title: 'BTC网格交易策略实战心得',
    content: '最近使用网格交易策略运行了两周，在BTC 60000-68000区间设置了20格，累计收益约3.2%。分享一些参数调优经验：间距不要设得太小，否则手续费会吃掉大部分利润。建议在波动率较高的时段运行。',
    tags: ['Grid', 'BTC', '实战'],
    likes: 24,
    comments: 8,
    views: 156,
  },
  {
    id: 2,
    author: 'QuantDev',
    type: '策略分享',
    time: '1天前',
    title: '分享一个高夏普比率的均值回归策略',
    content: '基于布林带+RSI的均值回归策略，回测夏普比率达到2.1，最大回撤5.8%。适用于ETH/USDT 4小时级别，参数设置：BB周期20，标准差2，RSI超卖30/超买70。代码已开源。',
    tags: ['MeanReversion', 'ETH', 'AI'],
    likes: 42,
    comments: 15,
    views: 320,
  },
];

const tags = [
  { name: 'Grid', count: 12, color: 'blue' },
  { name: 'DCA', count: 8, color: 'green' },
  { name: 'Trend', count: 6, color: 'yellow' },
  { name: 'AI', count: 5, color: 'purple' },
  { name: 'BTC', count: 15, color: 'orange' },
  { name: 'ETH', count: 9, color: 'blue' },
  { name: 'Momentum', count: 4, color: 'pink' },
  { name: 'MeanReversion', count: 3, color: 'gray' },
];

const stats = [
  { label: '总帖子数', value: '5', icon: FileText, color: 'bg-blue-100 text-blue-600' },
  { label: '社区用户', value: '5', icon: Users, color: 'bg-green-100 text-green-600' },
  { label: '今日新帖', value: '0', icon: Calendar, color: 'bg-orange-100 text-orange-600' },
  { label: '热门标签', value: '8', icon: Tag, color: 'bg-purple-100 text-purple-600' },
];

export const Market: React.FC = () => {
  const [activeSort, setActiveSort] = useState<'latest' | 'hot' | 'mostLiked'>('latest');

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">交易广场</h2>
        <button className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
          <Plus className="w-5 h-5" />
          <span className="text-sm font-medium">发布帖子</span>
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">筛选</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">帖子类型</label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                  <option>全部类型</option>
                  <option>交易心得</option>
                  <option>策略分享</option>
                  <option>市场分析</option>
                </select>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">热门标签</h3>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag, idx) => (
                <button
                  key={idx}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    tag.color === 'blue' ? 'bg-blue-100 text-blue-700 hover:bg-blue-200' :
                    tag.color === 'green' ? 'bg-green-100 text-green-700 hover:bg-green-200' :
                    tag.color === 'yellow' ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200' :
                    tag.color === 'purple' ? 'bg-purple-100 text-purple-700 hover:bg-purple-200' :
                    tag.color === 'orange' ? 'bg-orange-100 text-orange-700 hover:bg-orange-200' :
                    tag.color === 'pink' ? 'bg-pink-100 text-pink-700 hover:bg-pink-200' :
                    'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  #{tag.name} ({tag.count})
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 p-3 shadow-sm">
            <div className="flex space-x-1">
              {[
                { id: 'latest', label: '最新', icon: Clock },
                { id: 'hot', label: '热门', icon: Eye },
                { id: 'mostLiked', label: '点赞最多', icon: Heart },
              ].map((sort) => {
                const Icon = sort.icon;
                return (
                  <button
                    key={sort.id}
                    onClick={() => setActiveSort(sort.id as any)}
                    className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 text-sm font-medium transition-colors rounded-lg ${
                      activeSort === sort.id
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-500 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{sort.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {posts.map((post) => (
            <div key={post.id} className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 font-semibold text-sm">{post.author[0]}</span>
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-semibold text-gray-800">{post.author}</span>
                    <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full">{post.type}</span>
                    <span className="text-xs text-gray-500">{post.time}</span>
                  </div>
                </div>
              </div>

              <h4 className="text-lg font-semibold text-gray-800 mb-2">{post.title}</h4>
              <p className="text-sm text-gray-600 mb-4 leading-relaxed">{post.content}</p>

              <div className="flex flex-wrap gap-2 mb-4">
                {post.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="text-xs px-2.5 py-1 bg-blue-50 text-blue-700 rounded-full font-medium"
                  >
                    #{tag}
                  </span>
                ))}
              </div>

              <div className="flex items-center space-x-6 text-sm text-gray-500">
                <button className="flex items-center space-x-1.5 hover:text-red-500 transition-colors">
                  <Heart className="w-4 h-4" />
                  <span>{post.likes}</span>
                </button>
                <button className="flex items-center space-x-1.5 hover:text-primary-600 transition-colors">
                  <MessageCircle className="w-4 h-4" />
                  <span>{post.comments}</span>
                </button>
                <div className="flex items-center space-x-1.5">
                  <Eye className="w-4 h-4" />
                  <span>{post.views}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
