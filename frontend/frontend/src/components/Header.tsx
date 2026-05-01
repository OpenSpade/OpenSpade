import React from 'react';
import { Bell, HelpCircle, Briefcase } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <h2 className="text-xl font-semibold text-gray-800">交易控制台</h2>
        <div className="flex items-center space-x-1.5 px-2.5 py-1 bg-success-50 rounded-full">
          <span className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></span>
          <span className="text-xs text-success-600">实时连接</span>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 px-3 py-1.5 bg-gray-50 rounded-lg">
          <Briefcase className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">¥1,234,567</span>
        </div>
        <button className="relative p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <Bell className="w-5 h-5 text-gray-600" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-danger-500 rounded-full"></span>
        </button>
        <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <HelpCircle className="w-5 h-5 text-gray-600" />
        </button>
      </div>
    </header>
  );
};
