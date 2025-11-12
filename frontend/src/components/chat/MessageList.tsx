'use client';

import React from 'react';
import { ChatMessage } from '@/types/api';

interface MessageListProps {
  messages: ChatMessage[];
}

export function MessageList({ messages }: MessageListProps) {
  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-background">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-center">
          <div className="text-6xl mb-4">💬</div>
          <h3 className="text-xl font-semibold text-fg mb-2">
            Welcome to ZiggyAI Chat
          </h3>
          <p className="text-fg-muted max-w-md">
            Ask me anything about market analysis, trading strategies, or financial insights. 
            I&apos;m powered by Ollama and ready to help!
          </p>
          <div className="mt-6 grid grid-cols-1 gap-2 text-sm">
            <div className="text-fg-muted">💡 Try asking:</div>
            <div className="text-fg-muted italic">&quot;What&apos;s the market sentiment today?&quot;</div>
            <div className="text-fg-muted italic">&quot;Analyze AAPL&apos;s recent performance&quot;</div>
            <div className="text-fg-muted italic">&quot;What are the current crypto trends?&quot;</div>
          </div>
        </div>
      ) : (
        messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))
      )}
    </div>
  );
}

interface MessageBubbleProps {
  message: ChatMessage;
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const timestamp = new Date(message.timestamp).toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  });

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[70%] ${isUser ? 'order-2' : 'order-1'}`}>
        <div
          className={`
            px-4 py-3 rounded-2xl shadow-sm
            ${isUser 
              ? 'bg-accent text-accent-fg ml-4' 
              : 'bg-surface border border-border mr-4'
            }
          `}
        >
          {message.isLoading ? (
            <div className="flex items-center space-x-2">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-fg-muted rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-fg-muted rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-fg-muted rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
              <span className="text-fg-muted text-sm">ZiggyAI is thinking...</span>
            </div>
          ) : (
            <>
              <div className="text-sm leading-relaxed whitespace-pre-wrap">
                {message.content}
              </div>
              
              {/* Show sources if available */}
              {message.sources && message.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-border/50">
                  <div className="text-xs text-fg-muted mb-1">Sources:</div>
                  <div className="space-y-1">
                    {message.sources.map((source, index) => (
                      <div key={index} className="text-xs text-fg-muted bg-surface/50 px-2 py-1 rounded">
                        {'\uD83D\uDCC4'} {source}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Show confidence if available */}
              {message.confidence !== undefined && (
                <div className="mt-2 flex items-center space-x-2">
                  <span className="text-xs text-fg-muted">Confidence:</span>
                  <div className="flex-1 bg-surface rounded-full h-1.5">
                    <div 
                      className="bg-accent h-1.5 rounded-full transition-all duration-300"
                      style={{ width: `${(message.confidence || 0) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-fg-muted font-medium">
                    {Math.round((message.confidence || 0) * 100)}%
                  </span>
                </div>
              )}
            </>
          )}
        </div>
        
        {/* Timestamp */}
        <div 
          className={`
            text-xs text-fg-muted mt-1 px-1
            ${isUser ? 'text-right' : 'text-left'}
          `}
        >
          {timestamp}
        </div>
      </div>
      
      {/* Avatar */}
      <div className={`
        w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
        ${isUser 
          ? 'bg-accent text-accent-fg order-1 ml-2' 
          : 'bg-surface border border-border order-2 mr-2'
        }
      `}>
        {isUser ? '\uD83D\uDC64' : '\uD83E\uDD16'}
      </div>
    </div>
  );
}