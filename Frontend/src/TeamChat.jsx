// TeamChat.jsx
import React, { useState, useEffect, useRef } from 'react';
import { fetchTeamMessages, createTeamMessage } from './api';

export default function TeamChat({ user, users }) {
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const chatEndRef = useRef(null);

  const loadMessages = () => {
    fetchTeamMessages().then(setMessages);
  };

  // Poll for new messages every 3 seconds
  useEffect(() => {
    loadMessages();
    const interval = setInterval(loadMessages, 3000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => { 
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    const msg = text;
    setText(''); // clear instantly for good UX
    await createTeamMessage(Number(user.id), msg);
    loadMessages();
  };

  const getUserName = (id) => users.find(u => u.id === id)?.name || 'Unknown';

  return (
    <div className="tf-card" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 100px)' }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
        <h3 style={{ margin: 0, fontSize: 16, color: '#0f172a' }}>Global Team Chat</h3>
        <p style={{ margin: 0, fontSize: 12, color: '#64748b' }}>Visible to all team members.</p>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {messages.map(m => {
          const isMe = m.user_id === user.id;
          return (
            <div key={m.id} style={{ display: 'flex', flexDirection: 'column', alignItems: isMe ? 'flex-end' : 'flex-start' }}>
              <span style={{ fontSize: 11, color: '#94a3b8', marginBottom: 4, marginLeft: 2, marginRight: 2 }}>
                {isMe ? 'You' : getUserName(m.user_id)} • {new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
              <div style={{ 
                background: isMe ? '#2563eb' : '#f1f5f9', 
                color: isMe ? '#fff' : '#1e293b', 
                padding: '8px 14px', borderRadius: 16, maxWidth: '70%', fontSize: 13 
              }}>
                {m.text}
              </div>
            </div>
          );
        })}
        <div ref={chatEndRef} />
      </div>

      <form onSubmit={handleSend} style={{ padding: 16, borderTop: '1px solid #e2e8f0', display: 'flex', gap: 10 }}>
        <input className="tf-field" placeholder="Type a message to the team..." value={text} onChange={e => setText(e.target.value)} style={{ flex: 1 }} />
        <button className="tf-btn-primary" type="submit">Send</button>
      </form>
    </div>
  );
}