'use client';

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { PageLayout } from '@/components/layout/PageLayout';
import { TRADING_GLOSSARY, GlossaryTerm } from '@/utils/glossary';
import Link from 'next/link';
import { Search, Book, TrendingUp, Shield, Lightbulb, ArrowRight } from 'lucide-react';

export default function HelpPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const categories = {
    all: 'All Terms',
    basics: 'Trading Basics',
    risk: 'Risk & Metrics',
    orders: 'Order Types',
    analysis: 'Analysis & Signals'
  };

  const categoryMap: Record<string, string[]> = {
    basics: ['portfolio', 'watchlist', 'quote', 'long', 'short', 'volume', 'spread', 'pnl', 'return'],
    risk: ['sharpeRatio', 'beta', 'alpha', 'volatility', 'maxDrawdown', 'sortinoRatio', 'diversification', 'exposure'],
    orders: ['marketOrder', 'limitOrder'],
    analysis: ['signal', 'sentiment', 'vix']
  };

  const getFilteredTerms = (): [string, GlossaryTerm][] => {
    let entries = Object.entries(TRADING_GLOSSARY);

    // Filter by category
    if (selectedCategory !== 'all') {
      const categoryKeys = categoryMap[selectedCategory] || [];
      entries = entries.filter(([key]) => categoryKeys.includes(key));
    }

    // Filter by search term
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      entries = entries.filter(([, term]) => 
        term.term.toLowerCase().includes(search) ||
        term.shortDefinition.toLowerCase().includes(search) ||
        term.longDefinition.toLowerCase().includes(search)
      );
    }

    return entries;
  };

  const quickTips = [
    {
      icon: <Lightbulb className="w-5 h-5" />,
      title: 'Start with Paper Trading',
      description: 'Practice with fake money before risking real capital'
    },
    {
      icon: <Shield className="w-5 h-5" />,
      title: 'Diversify Your Portfolio',
      description: 'Don&apos;t put all your eggs in one basket - spread your investments'
    },
    {
      icon: <TrendingUp className="w-5 h-5" />,
      title: 'Check Confidence Scores',
      description: 'Higher confidence signals (70%+) are more reliable'
    },
    {
      icon: <Book className="w-5 h-5" />,
      title: 'Learn As You Go',
      description: 'Hover over terms with info icons to see explanations'
    }
  ];

  const filteredTerms = getFilteredTerms();

  return (
    <PageLayout title="Help & Glossary" subtitle="Learn trading terminology and how to use ZiggyAI">
      <div className="space-y-6">
        {/* Quick Tips */}
        <Card>
          <CardHeader>
            <CardTitle>💡 Quick Tips for Beginners</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {quickTips.map((tip, index) => (
                <div key={index} className="flex flex-col space-y-2 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                  <div className="text-blue-600 dark:text-blue-400">
                    {tip.icon}
                  </div>
                  <h3 className="font-semibold text-sm">{tip.title}</h3>
                  <p className="text-xs text-fg-muted">{tip.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Getting Started Guide */}
        <Card>
          <CardHeader>
            <CardTitle>🚀 Getting Started</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                  1
                </div>
                <div>
                  <h3 className="font-semibold">Explore the Dashboard</h3>
                  <p className="text-sm text-fg-muted">Familiarize yourself with the main overview page showing your portfolio, watchlist, and signals.</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                  2
                </div>
                <div>
                  <h3 className="font-semibold">Add Stocks to Your Watchlist</h3>
                  <p className="text-sm text-fg-muted">Start by adding 3-5 stocks you&apos;ve heard of (like AAPL, MSFT, GOOGL) to track their prices and get AI signals.</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                  3
                </div>
                <div>
                  <h3 className="font-semibold">Review Trading Signals</h3>
                  <p className="text-sm text-fg-muted">Check the AI-generated buy/sell/hold recommendations and read the explanations for each signal.</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                  4
                </div>
                <div>
                  <h3 className="font-semibold">Practice with Paper Trading</h3>
                  <p className="text-sm text-fg-muted">Use paper trading mode to practice without risking real money. Build confidence before trading for real.</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Trading Glossary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>📖 Trading Glossary</span>
              <div className="text-sm font-normal text-fg-muted">
                {filteredTerms.length} terms
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* Search and Filter */}
            <div className="space-y-4 mb-6">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search for a term..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-fg-primary focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="flex flex-wrap gap-2">
                {Object.entries(categories).map(([key, label]) => (
                  <button
                    key={key}
                    onClick={() => setSelectedCategory(key)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      selectedCategory === key
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 dark:bg-gray-800 text-fg-primary hover:bg-gray-200 dark:hover:bg-gray-700'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Terms List */}
            <div className="space-y-4">
              {filteredTerms.length === 0 ? (
                <div className="text-center py-8 text-fg-muted">
                  No terms found matching &ldquo;{searchTerm}&rdquo;
                </div>
              ) : (
                filteredTerms.map(([key, term]) => (
                  <div
                    key={key}
                    className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-300 dark:hover:border-blue-700 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-lg font-semibold text-fg-primary">
                        {term.term}
                      </h3>
                      {term.goodRange && (
                        <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 px-2 py-1 rounded">
                          {term.goodRange}
                        </span>
                      )}
                    </div>
                    
                    <p className="text-sm font-medium text-blue-600 dark:text-blue-400 mb-2">
                      {term.shortDefinition}
                    </p>
                    
                    <p className="text-sm text-fg-muted mb-3">
                      {term.longDefinition}
                    </p>
                    
                    {term.example && (
                      <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                        <p className="text-xs font-medium text-fg-muted mb-1">Example:</p>
                        <p className="text-sm text-fg-primary">{term.example}</p>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Additional Resources */}
        <Card>
          <CardHeader>
            <CardTitle>📚 Additional Resources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div>
                  <h3 className="font-semibold text-fg-primary">Complete User Guide</h3>
                  <p className="text-sm text-fg-muted">Comprehensive guide in the main README at the root of the repository</p>
                </div>
                <Book className="w-5 h-5 text-gray-400" />
              </div>
              
              <Link
                href="/learning"
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors group"
              >
                <div>
                  <h3 className="font-semibold text-fg-primary">Learning Center</h3>
                  <p className="text-sm text-fg-muted">Interactive tutorials and feedback system</p>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400" />
              </Link>
              
              <Link
                href="/paper-trading"
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors group"
              >
                <div>
                  <h3 className="font-semibold text-fg-primary">Paper Trading</h3>
                  <p className="text-sm text-fg-muted">Practice trading with virtual money</p>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400" />
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Safety Reminders */}
        <Card className="border-yellow-300 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/20">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
              <span>⚠️ Important Safety Reminders</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              <li className="flex items-start space-x-2">
                <span className="text-yellow-600 dark:text-yellow-400">•</span>
                <span>Never invest money you can&apos;t afford to lose</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-yellow-600 dark:text-yellow-400">•</span>
                <span>AI signals are suggestions, not guarantees - always do your own research</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-yellow-600 dark:text-yellow-400">•</span>
                <span>Start with paper trading to practice without risk</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-yellow-600 dark:text-yellow-400">•</span>
                <span>Diversify your portfolio - don&apos;t put all money in one stock</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-yellow-600 dark:text-yellow-400">•</span>
                <span>Be patient - good investing takes time, not minutes</span>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </PageLayout>
  );
}
