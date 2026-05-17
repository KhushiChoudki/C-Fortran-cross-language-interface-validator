import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Copy, Check } from 'lucide-react';
import axios from 'axios';

const CodeBlock = ({ content }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="code-block-container">
      <div className="code-block-header">
        <span className="lang-label">fortran</span>
        <button className="copy-btn" onClick={handleCopy}>
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? 'Copied!' : 'Copy code'}
        </button>
      </div>
      <pre>
        <code>{content}</code>
      </pre>
    </div>
  );
};

export default function AIGeneratorTab() {
  const [messages, setMessages] = useState([
    { role: 'ai', content: 'Hello! Paste your C header code here, and I will generate the Fortran BIND(C) interfaces for you.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = input;
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://127.0.0.1:5000/api/generate', { prompt: userMsg });
      setMessages(prev => [...prev, { role: 'ai', content: response.data.generated }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'ai', content: 'Sorry, I encountered an error communicating with the server.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatMessage = (content) => {
    if (content.includes('module') || content.includes('! Auto')) {
      return <CodeBlock content={content} />;
    }
    return <p>{content}</p>;
  };

  return (
    <div className="ai-tab">
      <div className="chat-history">
        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-msg ${msg.role}`}>
            <div className="avatar">
              {msg.role === 'ai' ? <Bot size={20} /> : <User size={20} />}
            </div>
            <div className="bubble">
              {formatMessage(msg.content)}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="chat-msg ai">
            <div className="avatar"><Bot size={20} /></div>
            <div className="bubble">
              <span className="spinner" style={{display:'inline-block'}}>⟳</span> Generating...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input-container">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Paste C code here..."
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
        />
        <button 
          className="send-btn" 
          onClick={handleSend} 
          disabled={isLoading || !input.trim()}
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
