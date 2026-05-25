import { useState, useEffect } from 'react'
import './index.css'
import { FileText, UtensilsCrossed, MessageSquare, Activity, Sun, Moon } from 'lucide-react'
import ReportTab from './tabs/ReportTab'
import FoodTab from './tabs/FoodTab'
import AdviceTab from './tabs/AdviceTab'

type Tab = 'report' | 'food' | 'advice'

export default function App() {
  const [tab, setTab] = useState<Tab>('advice')
  const [dark, setDark] = useState(false)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
  }, [dark])

  return (
    <div className="app">
      {/* Top Navbar */}
      <nav className="navbar">
        <div className="navbar-brand">
          <div className="navbar-logo">
            <Activity size={18} color="#FFFFFF" strokeWidth={2.5} />
          </div>
          <div>
            <p className="navbar-title">DietaryAI</p>
            <p className="navbar-subtitle">Personalised dietary guidance</p>
          </div>
        </div>
        <div className="navbar-right">
          <span className="navbar-badge">COM6016M · Research Artefact</span>
          <button
            className="theme-toggle"
            onClick={() => setDark(d => !d)}
            title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {dark ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </nav>

      {/* Page content */}
      <div className="container">
        {tab === 'advice' && <AdviceTab />}
        {tab === 'food' && <FoodTab />}
        {tab === 'report' && <ReportTab />}
      </div>

      {/* Bottom Glass Tab Bar */}
      <div className="bottom-tab-bar">
        <div className="bottom-tab-inner">
          <button
            className={`tab-btn ${tab === 'advice' ? 'active' : ''}`}
            onClick={() => setTab('advice')}
          >
            <span className="tab-icon"><MessageSquare size={20} /></span>
            <span className="tab-btn-label">Ask AI</span>
          </button>
          <button
            className={`tab-btn ${tab === 'food' ? 'active' : ''}`}
            onClick={() => setTab('food')}
          >
            <span className="tab-icon"><UtensilsCrossed size={20} /></span>
            <span className="tab-btn-label">Food Check</span>
          </button>
          <button
            className={`tab-btn ${tab === 'report' ? 'active' : ''}`}
            onClick={() => setTab('report')}
          >
            <span className="tab-icon"><FileText size={20} /></span>
            <span className="tab-btn-label">Report</span>
          </button>
        </div>
      </div>
    </div>
  )
}
