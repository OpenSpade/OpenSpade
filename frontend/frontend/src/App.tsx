import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { AIAssistant } from './components/AIAssistant';
import { Dashboard } from './pages/Dashboard';
import { Strategy } from './pages/Strategy';
import { AIStrategy } from './pages/AIStrategy';
import { Monitor } from './pages/Monitor';
import { Backtest } from './pages/Backtest';
import { Portfolio } from './pages/Portfolio';
import { Risk } from './pages/Risk';
import { TrendCenter } from './pages/TrendCenter';
import { RiskCenter } from './pages/RiskCenter';
import { Fee } from './pages/Fee';
import { Share } from './pages/Share';
import { Market } from './pages/Market';
import { Settings } from './pages/Settings';

type PageType = 
  | 'dashboard'
  | 'strategy'
  | 'ai-strategy'
  | 'monitor'
  | 'backtest'
  | 'portfolio'
  | 'risk'
  | 'trend-center'
  | 'risk-center'
  | 'fee'
  | 'share'
  | 'market'
  | 'settings';

const pageComponents: Record<PageType, React.FC> = {
  dashboard: Dashboard,
  strategy: Strategy,
  'ai-strategy': AIStrategy,
  monitor: Monitor,
  backtest: Backtest,
  portfolio: Portfolio,
  risk: Risk,
  'trend-center': TrendCenter,
  'risk-center': RiskCenter,
  fee: Fee,
  share: Share,
  market: Market,
  settings: Settings,
};

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<PageType>('dashboard');

  const PageComponent = pageComponents[activeTab];

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar activeTab={activeTab} onTabChange={(tab) => setActiveTab(tab as PageType)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto">
          <PageComponent />
        </main>
      </div>
      <AIAssistant />
    </div>
  );
};

export default App;
