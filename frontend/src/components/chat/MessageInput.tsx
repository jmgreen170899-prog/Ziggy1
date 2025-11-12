'use client';

import React, { useState, useRef, KeyboardEvent } from 'react';
import { Button } from '@/components/ui/Button';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export function MessageInput({ onSendMessage, isLoading, disabled = false }: MessageInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !isLoading && !disabled) {
      onSendMessage(trimmedMessage);
      setMessage('');
      resetTextareaHeight();
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    adjustTextareaHeight();
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const newHeight = Math.min(textarea.scrollHeight, 120); // Max height of ~6 lines
      textarea.style.height = `${newHeight}px`;
    }
  };

  const resetTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
    }
  };

  const canSend = message.trim().length > 0 && !isLoading && !disabled;

  return (
    <div className="bg-surface p-4 border-t border-border">
      <div className="flex items-end space-x-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={isLoading ? "ZiggyAI is responding..." : "Ask ZiggyAI anything about markets, trading, or finance..."}
            disabled={isLoading || disabled}
            className="
              w-full px-4 py-3 pr-12 
              bg-background border border-border rounded-2xl
              resize-none overflow-y-auto
              focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent
              disabled:opacity-50 disabled:cursor-not-allowed
              text-sm leading-relaxed
              placeholder:text-fg-muted
            "
            rows={1}
            style={{ minHeight: '48px' }}
          />
          
          {/* Character counter for long messages */}
          {message.length > 800 && (
            <div className="absolute bottom-1 right-12 text-xs text-fg-muted">
              {message.length}/1000
            </div>
          )}
        </div>
        
        <Button
          onClick={handleSend}
          disabled={!canSend}
          className="
            px-4 py-3 h-12 min-w-[48px]
            bg-accent hover:bg-accent/90 
            text-accent-fg
            disabled:opacity-50 disabled:cursor-not-allowed
            rounded-2xl transition-all duration-200
            flex items-center justify-center
          "
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-accent-fg/30 border-t-accent-fg rounded-full animate-spin" />
          ) : (
            <svg 
              className="w-5 h-5" 
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
            </svg>
          )}
        </Button>
      </div>
      
      {/* Quick suggestions */}
      {message.length === 0 && !isLoading && (
        <div className="flex flex-wrap gap-2 mt-3">
          <QuickSuggestion 
            text="Market outlook today?" 
            onClick={() => setMessage("What's the current market outlook and sentiment?")}
          />
          <QuickSuggestion 
            text="Analyze AAPL" 
            onClick={() => setMessage("Can you analyze AAPL's recent performance and provide insights?")}
          />
          <QuickSuggestion 
            text="Crypto trends" 
            onClick={() => setMessage("What are the current cryptocurrency market trends?")}
          />
          <QuickSuggestion 
            text="Trading strategies" 
            onClick={() => setMessage("What trading strategies would you recommend for the current market?")}
          />
        </div>
      )}
      
      {/* Help text */}
      <div className="text-xs text-fg-muted mt-2 flex items-center justify-between">
        <span>Press Enter to send, Shift+Enter for new line</span>
        <span className="flex items-center space-x-1">
          <span>Powered by</span>
          <span className="font-medium text-accent">Ollama</span>
        </span>
      </div>
    </div>
  );
}

interface QuickSuggestionProps {
  text: string;
  onClick: () => void;
}

function QuickSuggestion({ text, onClick }: QuickSuggestionProps) {
  return (
    <button
      onClick={onClick}
      className="
        px-3 py-1.5 text-sm
        bg-surface border border-border rounded-full
        hover:bg-surface-hover hover:border-accent/30
        transition-all duration-200
        text-fg-muted hover:text-fg
      "
    >
      {text}
    </button>
  );
}