import { useState } from 'react';
import AIGeneratorTab from './components/AIGeneratorTab';
import IDEValidatorTab from './components/IDEValidatorTab';
import TestCasesTab from './components/TestCasesTab';
import { Terminal, Code2, ListChecks } from 'lucide-react';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('testcases');

  return (
    <div className="app-container">
      <header className="header">
        <div className="logo">
          <span>FC</span>Validator
        </div>
        <div className="tabs">
          <button 
            className={`tab-btn ${activeTab === 'testcases' ? 'active' : ''}`}
            onClick={() => setActiveTab('testcases')}
          >
            <ListChecks size={18} /> Test Cases
          </button>
          <button 
            className={`tab-btn ${activeTab === 'ai' ? 'active' : ''}`}
            onClick={() => setActiveTab('ai')}
          >
            <Terminal size={18} /> AI Generator
          </button>
          <button 
            className={`tab-btn ${activeTab === 'ide' ? 'active' : ''}`}
            onClick={() => setActiveTab('ide')}
          >
            <Code2 size={18} /> IDE Validator
          </button>
        </div>
      </header>
      
      <main className="main-content">
        <div style={{ display: activeTab === 'testcases' ? 'block' : 'none', height: '100%' }}>
          <TestCasesTab />
        </div>
        <div style={{ display: activeTab === 'ai' ? 'block' : 'none', height: '100%' }}>
          <AIGeneratorTab />
        </div>
        <div style={{ display: activeTab === 'ide' ? 'block' : 'none', height: '100%' }}>
          <IDEValidatorTab />
        </div>
      </main>
    </div>
  );
}

export default App;
