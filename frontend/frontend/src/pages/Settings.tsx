import React, { useState } from 'react';
import { Settings as SettingsIcon, User, Bell, Shield, Code, TrendingUp, Save, RefreshCw } from 'lucide-react';

export const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'general' | 'trading' | 'notifications' | 'security' | 'api'>('general');
  const [darkMode, setDarkMode] = useState(false);
  const [compactLayout, setCompactLayout] = useState(false);
  const [realTimeData, setRealTimeData] = useState(true);

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">系统设置</h2>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="border-b border-gray-200">
          <div className="flex space-x-1 px-5">
            {[
              { id: 'general', label: '通用设置', icon: SettingsIcon },
              { id: 'trading', label: '交易设置', icon: TrendingUp },
              { id: 'notifications', label: '通知设置', icon: Bell },
              { id: 'security', label: '安全设置', icon: Shield },
              { id: 'api', label: 'API设置', icon: Code },
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
          {activeTab === 'general' && (
            <div className="space-y-6 max-w-3xl">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">基本信息</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">用户名</label>
                    <input
                      type="text"
                      defaultValue="Trader"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">邮箱</label>
                    <input
                      type="email"
                      defaultValue="trader@example.com"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">时区</label>
                    <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                      <option>Asia/Shanghai (UTC+8)</option>
                      <option>America/New_York (UTC-5)</option>
                      <option>Europe/London (UTC+0)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">语言</label>
                    <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                      <option>中文简体</option>
                      <option>English</option>
                    </select>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">界面设置</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between py-3 border-b border-gray-100">
                    <div>
                      <p className="text-sm font-medium text-gray-800">深色模式</p>
                      <p className="text-xs text-gray-500">启用深色主题界面</p>
                    </div>
                    <button
                      onClick={() => setDarkMode(!darkMode)}
                      className={`w-12 h-6 rounded-full transition-colors ${
                        darkMode ? 'bg-primary-600' : 'bg-gray-300'
                      }`}
                    >
                      <div
                        className={`w-4 h-4 rounded-full bg-white transition-transform ${
                          darkMode ? 'translate-x-7' : 'translate-x-1'
                        }`}
                      ></div>
                    </button>
                  </div>
                  <div className="flex items-center justify-between py-3 border-b border-gray-100">
                    <div>
                      <p className="text-sm font-medium text-gray-800">紧凑布局</p>
                      <p className="text-xs text-gray-500">使用更紧凑的界面布局</p>
                    </div>
                    <button
                      onClick={() => setCompactLayout(!compactLayout)}
                      className={`w-12 h-6 rounded-full transition-colors ${
                        compactLayout ? 'bg-primary-600' : 'bg-gray-300'
                      }`}
                    >
                      <div
                        className={`w-4 h-4 rounded-full bg-white transition-transform ${
                          compactLayout ? 'translate-x-7' : 'translate-x-1'
                        }`}
                      ></div>
                    </button>
                  </div>
                  <div className="flex items-center justify-between py-3 border-b border-gray-100">
                    <div>
                      <p className="text-sm font-medium text-gray-800">实时数据</p>
                      <p className="text-xs text-gray-500">启用实时价格更新</p>
                    </div>
                    <button
                      onClick={() => setRealTimeData(!realTimeData)}
                      className={`w-12 h-6 rounded-full transition-colors ${
                        realTimeData ? 'bg-primary-600' : 'bg-gray-300'
                      }`}
                    >
                      <div
                        className={`w-4 h-4 rounded-full bg-white transition-transform ${
                          realTimeData ? 'translate-x-7' : 'translate-x-1'
                        }`}
                      ></div>
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-gray-100">
                <button className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors flex items-center space-x-2">
                  <RefreshCw className="w-4 h-4" />
                  <span>重置</span>
                </button>
                <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center space-x-2">
                  <Save className="w-4 h-4" />
                  <span>保存设置</span>
                </button>
              </div>
            </div>
          )}
          
          {activeTab === 'trading' && (
            <div className="flex items-center justify-center h-48">
              <p className="text-gray-500">交易设置区域</p>
            </div>
          )}
          
          {activeTab === 'notifications' && (
            <div className="flex items-center justify-center h-48">
              <p className="text-gray-500">通知设置区域</p>
            </div>
          )}
          
          {activeTab === 'security' && (
            <div className="flex items-center justify-center h-48">
              <p className="text-gray-500">安全设置区域</p>
            </div>
          )}
          
          {activeTab === 'api' && (
            <div className="flex items-center justify-center h-48">
              <p className="text-gray-500">API设置区域</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
