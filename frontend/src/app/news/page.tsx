'use client';

import React, { useState, useEffect } from 'react';
import { RequireAuth } from '@/routes/RequireAuth';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { formatDateTime } from '@/utils';
import apiClient from '@/services/api';
import type { NewsItem } from '@/types/api';
import { guardRealData } from '@/lib/guardRealData';

interface NewsCardProps {
  news: NewsItem;
  onClick?: () => void;
}

function NewsCard({ news, onClick }: NewsCardProps) {
  const getSentimentColor = (sentiment?: string) => {
    switch (sentiment) {
      case 'positive': return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-300';
      case 'negative': return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-300';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-800 dark:text-gray-300';
    }
  };

  const getSentimentIcon = (sentiment?: string) => {
    switch (sentiment) {
      case 'positive': return '📈';
      case 'negative': return '📉';
      default: return '📊';
    }
  };

  return (
    <Card className="card-elevated cursor-pointer group" onClick={onClick}>
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          <div className="text-4xl p-3 bg-gray-50 dark:bg-gray-800 rounded-xl group-hover:scale-110 transition-transform">
            {getSentimentIcon(news.sentiment)}
          </div>
          
          <div className="flex-1">
            <div className="flex items-start justify-between mb-3">
              <h3 className="font-bold text-xl leading-tight pr-4 text-fg group-hover:text-accent transition-colors">
                {news.title}
              </h3>
              {news.sentiment && (
                <span className={`px-3 py-1 rounded-full text-xs font-bold whitespace-nowrap border-2 ${getSentimentColor(news.sentiment)}`}>
                  {news.sentiment.toUpperCase()}
                </span>
              )}
            </div>
            
            <p className="text-fg-muted text-base mb-4 leading-relaxed">
              {news.summary}
            </p>
            
            <div className="flex items-center justify-between pt-3 border-t border-border">
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-fg">{news.source}</span>
                </div>
                <span className="text-border" aria-hidden>•</span>
                <div className="flex items-center gap-1.5 text-fg-muted">
                  <span className="status-dot status-dot-success"></span>
                  <span className="font-medium">{formatDateTime(news.published_date)}</span>
                </div>
                {news.sentiment_score && (
                  <>
                    <span className="text-border" aria-hidden>•</span>
                    <span className="font-semibold">Score: {news.sentiment_score > 0 ? '+' : ''}{news.sentiment_score.toFixed(2)}</span>
                  </>
                )}
              </div>
              
              {news.symbols && news.symbols.length > 0 && (
                <div className="flex gap-2">
                  {news.symbols.slice(0, 3).map(symbol => (
                    <span key={symbol} className="px-2 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-md text-xs font-bold border border-blue-200 dark:border-blue-700">
                      {symbol}
                    </span>
                  ))}
                  {news.symbols.length > 3 && (
                    <span className="text-fg-muted font-semibold text-xs">+{news.symbols.length - 3}</span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface NewsFiltersProps {
  selectedSentiment: string;
  selectedSource: string;
  onSentimentChange: (sentiment: string) => void;
  onSourceChange: (source: string) => void;
  onRefresh: () => void;
}

function NewsFilters({ selectedSentiment, selectedSource, onSentimentChange, onSourceChange, onRefresh }: NewsFiltersProps) {
  const sentiments = ['all', 'positive', 'negative', 'neutral'];
  const sources = ['all', 'Reuters', 'Bloomberg', 'Wall Street Journal', 'CNBC', 'MarketWatch', 'Financial Times'];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Filters & Controls</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2 block">
              Sentiment
            </label>
            <select
              value={selectedSentiment}
              onChange={(e) => onSentimentChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
            >
              {sentiments.map(sentiment => (
                <option key={sentiment} value={sentiment}>
                  {sentiment === 'all' ? 'All Sentiment' : sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2 block">
              Source
            </label>
            <select
              value={selectedSource}
              onChange={(e) => onSourceChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
            >
              {sources.map(source => (
                <option key={source} value={source}>
                  {source === 'all' ? 'All Sources' : source}
                </option>
              ))}
            </select>
          </div>

          <Button onClick={onRefresh} className="w-full" variant="ghost">
            🔄 Refresh News
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

interface TrendingTopicsProps {
  topics: Array<{ topic: string; count: number; sentiment: number }>;
}

function TrendingTopics({ topics }: TrendingTopicsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Trending Topics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {topics.map((topic, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div>
                <div className="font-medium text-sm">{topic.topic}</div>
                <div className="text-xs text-gray-500">{topic.count} articles</div>
              </div>
              <div className={`text-sm font-medium ${topic.sentiment > 0.2 ? 'text-green-600' : topic.sentiment < -0.2 ? 'text-red-600' : 'text-gray-600'}`}>
                {topic.sentiment > 0 ? '+' : ''}{topic.sentiment.toFixed(2)}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default function NewsPage() {
  const [selectedSentiment, setSelectedSentiment] = useState('all');
  const [selectedSource, setSelectedSource] = useState('all');
  const [selectedNews, setSelectedNews] = useState<NewsItem | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [newsData, setNewsData] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadNews = async () => {
    try {
      setLoading(true);
      setError(null);
      const news = await apiClient.getNews();
      setNewsData(news);
    } catch (err) {
      console.error('Failed to load news:', err);
      setError('Failed to load news. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNews();
  }, []);

  if (process.env.NODE_ENV === 'development' && newsData.length > 0) {
    guardRealData('NewsList', [newsData[0]?.title || '', newsData[0]?.summary || '']);
  }

  const filteredNews = newsData.filter(news => {
    if (selectedSentiment !== 'all' && news.sentiment !== selectedSentiment) return false;
    if (selectedSource !== 'all' && news.source !== selectedSource) return false;
    return true;
  });

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadNews();
    setRefreshing(false);
  };

  const handleNewsClick = (news: NewsItem) => {
    setSelectedNews(news);
  };

  const derivedTrendingTopics = React.useMemo(() => {
    // Derive simple topics by counting symbol mentions across loaded news
    const counts: Record<string, { count: number; sentiment: number }> = {};
    for (const item of newsData) {
      const syms = item.symbols || [];
      for (const s of syms) {
        counts[s] = counts[s] || { count: 0, sentiment: 0 };
        counts[s].count += 1;
        counts[s].sentiment += (item.sentiment === 'positive' ? 1 : item.sentiment === 'negative' ? -1 : 0);
      }
    }
    const arr = Object.entries(counts).map(([topic, v]) => ({ topic, count: v.count, sentiment: v.count ? v.sentiment / v.count : 0 }));
    return arr.sort((a,b) => b.count - a.count).slice(0, 8);
  }, [newsData]);

  return (
    <RequireAuth>
      <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Market News</h1>
          <p className="text-gray-500 dark:text-gray-400">
            Real-time financial news with AI sentiment analysis
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            onClick={handleRefresh}
            disabled={refreshing}
            variant="ghost"
          >
            {refreshing ? '🔄' : '↻'} Refresh
          </Button>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* News Articles - Main Column */}
        <div className="lg:col-span-3 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Latest Articles</h2>
            <span className="text-sm text-gray-500">{filteredNews.length} articles</span>
          </div>
          
          {loading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Card key={i} className="animate-pulse">
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
                      <div className="flex-1 space-y-2">
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : error ? (
            <Card>
              <CardContent className="p-6 text-center">
                <div className="text-red-500 mb-2">⚠️</div>
                <div className="text-red-600 dark:text-red-400 mb-4">{error}</div>
                <Button onClick={loadNews} variant="outline">
                  Try Again
                </Button>
              </CardContent>
            </Card>
          ) : filteredNews.length === 0 ? (
            <Card>
              <CardContent className="p-6 text-center">
                <div className="text-gray-400 mb-2">📰</div>
                <div className="text-gray-600 dark:text-gray-400">No news articles found matching your filters.</div>
              </CardContent>
            </Card>
          ) : (
            filteredNews.map(news => (
              <NewsCard 
                key={news.id} 
                news={news} 
                onClick={() => handleNewsClick(news)}
              />
            ))
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <NewsFilters
            selectedSentiment={selectedSentiment}
            selectedSource={selectedSource}
            onSentimentChange={setSelectedSentiment}
            onSourceChange={setSelectedSource}
            onRefresh={handleRefresh}
          />
          
          <TrendingTopics topics={derivedTrendingTopics} />
        </div>
      </div>

      {/* News Detail Modal */}
      {selectedNews && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <CardHeader>
              <div className="flex items-start justify-between">
                <CardTitle className="text-xl leading-tight pr-4">{selectedNews.title}</CardTitle>
                <Button onClick={() => setSelectedNews(null)} variant="ghost" size="sm">
                  ✕
                </Button>
              </div>
              <div className="text-sm text-gray-500 mt-2">
                {selectedNews.source} • {formatDateTime(selectedNews.published_date)}
              </div>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none dark:prose-invert">
                <p className="text-gray-600 dark:text-gray-400 font-medium mb-4">
                  {selectedNews.summary}
                </p>
                <p className="text-gray-800 dark:text-gray-200 leading-relaxed">
                  {selectedNews.content}
                </p>
              </div>
              
              {selectedNews.symbols && selectedNews.symbols.length > 0 && (
                <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                    Related Symbols:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {selectedNews.symbols.map(symbol => (
                      <span key={symbol} className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded text-sm">
                        {symbol}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
    </RequireAuth>
  );
}