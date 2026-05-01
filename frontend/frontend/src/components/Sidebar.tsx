import React from 'react';
import {
  LayoutDashboard,
  BarChart3,
  Wand2,
  Radio,
  TrendingUp,
  Wallet,
  Shield,
  AlertTriangle,
  CreditCard,
  Share2,
  Store,
  Settings,
  User,
  LineChart
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const menuItems = [
  { id: 'dashboard', label: '仪表板', icon: LayoutDashboard },
  { id: 'strategy', label: '策略管理', icon: BarChart3 },
  { id: 'ai-strategy', label: 'AI写策略', icon: Wand2 },
  { id: 'monitor', label: '内容监听', icon: Radio },
  { id: 'backtest', label: '回测分析', icon: TrendingUp },
  { id: 'portfolio', label: '投资组合', icon: Wallet },
  { id: 'risk', label: '风险管理', icon: Shield },
  { id: 'trend-center', label: '趋势中心', icon: LineChart },
  { id: 'risk-center', label: '风险中心', icon: AlertTriangle },
  { id: 'fee', label: '费率中心', icon: CreditCard },
  { id: 'share', label: '分享中心', icon: Share2 },
  { id: 'market', label: '交易广场', icon: Store },
  { id: 'settings', label: '系统设置', icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col h-screen">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">AI</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-800">OpenSpade</h1>
            <p className="text-xs text-gray-500">智能投资平台</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                isActive
                  ? 'bg-primary-50 text-primary-600 font-medium'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-sm">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-3 border-t border-gray-200">
        <div className="flex items-center space-x-3 px-3 py-2">
          <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
            <User className="w-4 h-4 text-gray-600" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-800 truncate">交易员</p>
            <p className="text-xs text-success-500">在线</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
