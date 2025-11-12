'use client';

import React, { useEffect, useRef } from 'react';
import { useChatStore } from '@/store';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { Button } from '@/components/ui/Button';

export function ChatInterface() {
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    sendRAGQuery,
    sendAgentQuery,
    clearMessages,
    setError
  } = useChatStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    try {
      await sendMessage(content);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleClearChat = () => {
    clearMessages();
  };

  const handleDismissError = () => {
    setError(null);
  };

  const handleRetryLastMessage = () => {
    const lastUserMessage = messages
      .filter(m => m.role === 'user')
      .pop();
    
    if (lastUserMessage) {
      handleSendMessage(lastUserMessage.content);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-blue-900">
      {/* Enhanced Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200/50 dark:border-gray-700/50 bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-white/20 backdrop-blur rounded-xl flex items-center justify-center shadow-lg">
            <span className="text-white text-xl">🤖</span>
          </div>
          <div>
            <h2 className="text-xl font-bold">ZiggyAI Assistant</h2>
            <p className="text-blue-100">
              Powered by Ollama • {messages.length} messages • AI Trading Analysis
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          {/* Enhanced Model switcher */}
          <div className="flex items-center space-x-2 bg-white/10 backdrop-blur rounded-lg p-1">
            <button
              onClick={() => sendRAGQuery('Test RAG query')}
              disabled={isLoading}
              className="
                px-4 py-2 text-sm font-medium rounded-md
                bg-white/20 text-white border border-white/30
                hover:bg-white/30 hover:border-white/50
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-all duration-200
              "
              title="Use RAG Query (Default)"
            >
              📊 RAG Mode
            </button>
            <button
              onClick={() => sendAgentQuery('Test agent query')}
              disabled={isLoading}
              className="
                px-4 py-2 text-sm font-medium rounded-md
                bg-white/20 text-white border border-white/30
                hover:bg-white/30 hover:border-white/50
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-all duration-200
              "
              title="Use Agent Query"
            >
              🤖 Agent Mode
            </button>
          </div>
          
          {/* Enhanced Clear chat button */}
          {messages.length > 0 && (
            <Button
              onClick={handleClearChat}
              className="bg-white/20 hover:bg-white/30 text-white border-white/30 hover:border-white/50"
              size="sm"
              title="Clear chat history"
            >
              🗑️ Clear
            </Button>
          )}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span className="text-red-700 text-sm">{error}</span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleRetryLastMessage}
                className="text-red-700 hover:text-red-800 text-sm underline"
              >
                Retry
              </button>
              <button
                onClick={handleDismissError}
                className="text-red-500 hover:text-red-700"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 min-h-0 relative bg-background">
        <MessageList messages={messages} />
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <MessageInput
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        disabled={!!error}
      />
    </div>
  );
}