'use client';

import { useEffect, useState } from 'react';

export default function WebSocketTest() {
  const [status, setStatus] = useState('Disconnected');
  const [messages, setMessages] = useState<string[]>([]);
  const [urlUsed, setUrlUsed] = useState<string>('');

  useEffect(() => {
    console.log('🔌 WebSocket Test: Starting connection...');
    // Build a robust default WS URL for testing
    const envUrl = (process.env.NEXT_PUBLIC_WS_URL || '').trim();
    const base = envUrl
      ? envUrl.replace(/\/$/, '')
      : (typeof window !== 'undefined' && window.location)
        ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
        : 'ws://localhost:8000';
    const wsUrl = `${base}/ws/market`;
    setUrlUsed(wsUrl);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('✅ WebSocket Test: Connected!');
      setStatus('Connected');
      setMessages(prev => [...prev, '✅ Connected to WebSocket']);
    };

    ws.onmessage = (event) => {
      console.log('📊 WebSocket Test: Message received:', event.data);
      try {
        const data = JSON.parse(event.data);
        setMessages(prev => [...prev, `📊 ${data.type}: ${data.symbol || 'unknown'}`]);
      } catch {
        setMessages(prev => [...prev, `📊 Raw: ${event.data.substring(0, 100)}`]);
      }
    };

    ws.onclose = () => {
      console.log('❌ WebSocket Test: Disconnected');
      setStatus('Disconnected');
      setMessages(prev => [...prev, '❌ WebSocket disconnected']);
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket Test: Error:', error);
      setMessages(prev => [...prev, '❌ WebSocket error occurred']);
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">🔍 WebSocket Connection Test</h1>
      
      <div className={`p-4 rounded mb-4 ${status === 'Connected' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
        Status: {status}
      </div>

      <div className="bg-gray-100 p-4 rounded">
        <h2 className="font-semibold mb-2">Messages ({messages.length})</h2>
        <div className="h-64 overflow-y-auto space-y-1">
          {messages.map((msg, idx) => (
            <div key={idx} className="text-sm font-mono">{msg}</div>
          ))}
        </div>
      </div>

      <div className="mt-4 text-sm text-gray-600">
        <p>Testing WS URL: {urlUsed || 'resolving…'}</p>
        <p>Check browser console for detailed logs</p>
      </div>
    </div>
  );
}