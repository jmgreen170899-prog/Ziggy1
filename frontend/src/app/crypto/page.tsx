'use client';

import React, { useState, useEffect } from 'react';
import { RequireAuth } from '@/routes/RequireAuth';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { PageLayout, ThemedButton, ThemedCard } from '@/components/layout/PageLayout';
import { formatCurrency, formatPercentage, getPriceColor } from '@/utils';
import { apiClient } from '@/services/api';
import type { CryptoPrice } from '@/types/api';

interface CryptoCardProps {
  crypto: CryptoPrice;
  viewMode: 'card' | 'table';
}

function CryptoCard({ crypto, viewMode }: CryptoCardProps) {
  if (viewMode === 'table') {
    return (
      <tr className="hover:bg-gray-50 dark:hover:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <td className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-orange-400 to-yellow-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
              #{crypto.rank}
            </div>
            <div>
              <div className="font-semibold">{crypto.symbol}</div>
              <div className="text-sm text-gray-500">{crypto.name}</div>
            </div>
          </div>
        </td>
        <td className="p-4 text-right">
          <div className="font-bold">{formatCurrency(crypto.price)}</div>
        </td>
        <td className="p-4 text-right">
          <div className={getPriceColor(crypto.change_24h)}>
            {crypto.change_24h >= 0 ? '+' : ''}{formatPercentage(crypto.change_percent_24h)}
          </div>
        </td>
        <td className="p-4 text-right">
          <div className="font-medium">
            {crypto.volume_24h > 0 ? `$${(crypto.volume_24h / 1000000000).toFixed(2)}B` : 'N/A'}
          </div>
        </td>
        <td className="p-4 text-right">
          <div className="font-medium">
            {crypto.market_cap > 0 ? `$${(crypto.market_cap / 1000000000).toFixed(1)}B` : 'N/A'}
          </div>
        </td>
      </tr>
    );
  }

  return (
    <Card className="hover:shadow-md transition-shadow cursor-pointer">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-400 to-yellow-500 rounded-full flex items-center justify-center text-white font-bold">
              #{crypto.rank}
            </div>
            <div>
              <div className="font-semibold text-lg">{crypto.symbol}</div>
              <div className="text-sm text-gray-500">{crypto.name}</div>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-xl font-bold">{formatCurrency(crypto.price)}</div>
            <div className={`text-sm ${getPriceColor(crypto.change_24h)}`}>
              {crypto.change_24h >= 0 ? '+' : ''}{formatPercentage(crypto.change_percent_24h)}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-gray-500 text-xs">24h Volume</div>
            <div className="font-medium">
              {crypto.volume_24h > 0 ? `$${(crypto.volume_24h / 1000000000).toFixed(2)}B` : 'N/A'}
            </div>
          </div>
          <div>
            <div className="text-gray-500 text-xs">Market Cap</div>
            <div className="font-medium">
              {crypto.market_cap > 0 ? `$${(crypto.market_cap / 1000000000).toFixed(1)}B` : 'N/A'}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface CryptoStatsProps {
  cryptoData: CryptoPrice[];
}

function CryptoStats({ cryptoData }: CryptoStatsProps) {
  const totalMarketCap = cryptoData.reduce((sum, crypto) => sum + crypto.market_cap, 0);
  const gainers = cryptoData.filter(crypto => crypto.change_percent_24h > 0).length;
  const losers = cryptoData.filter(crypto => crypto.change_percent_24h < 0).length;
  const avgChange = cryptoData.length > 0 
    ? cryptoData.reduce((sum, crypto) => sum + crypto.change_percent_24h, 0) / cryptoData.length 
    : 0;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <ThemedCard>
        <div className="text-center p-4">
          <div className="text-2xl font-bold">
            {totalMarketCap > 0 ? `$${(totalMarketCap / 1000000000000).toFixed(2)}T` : 'N/A'}
          </div>
          <div className="text-sm text-gray-500">Total Market Cap</div>
        </div>
      </ThemedCard>

      <ThemedCard>
        <div className="text-center p-4">
          <div className="text-2xl font-bold text-green-600">{gainers}</div>
          <div className="text-sm text-gray-500">Gainers (24h)</div>
        </div>
      </ThemedCard>

      <ThemedCard>
        <div className="text-center p-4">
          <div className="text-2xl font-bold text-red-600">{losers}</div>
          <div className="text-sm text-gray-500">Losers (24h)</div>
        </div>
      </ThemedCard>

      <ThemedCard>
        <div className="text-center p-4">
          <div className={`text-2xl font-bold ${getPriceColor(avgChange)}`}>
            {avgChange >= 0 ? '+' : ''}{formatPercentage(avgChange)}
          </div>
          <div className="text-sm text-gray-500">Avg Change (24h)</div>
        </div>
      </ThemedCard>
    </div>
  );
}

function CryptoNews() {
  const news = [
    {
      title: "Bitcoin Reaches New All-Time High as Institutional Adoption Grows",
      source: "CoinDesk",
      time: "2 hours ago",
      sentiment: "positive" as const
    },
    {
      title: "Ethereum 2.0 Staking Rewards Hit Record Levels",
      source: "CryptoSlate",
      time: "4 hours ago", 
      sentiment: "positive" as const
    },
    {
      title: "Regulatory Uncertainty Continues to Impact Crypto Markets",
      source: "Bloomberg",
      time: "6 hours ago",
      sentiment: "negative" as const
    },
    {
      title: "DeFi TVL Surpasses $100 Billion Milestone",
      source: "The Block",
      time: "8 hours ago",
      sentiment: "positive" as const
    }
  ];

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return '📈';
      case 'negative': return '📉';
      default: return '📊';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Crypto News</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {news.map((article, index) => (
            <div key={index} className="p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer">
              <div className="flex items-start gap-3">
                <span className="text-lg">{getSentimentIcon(article.sentiment)}</span>
                <div className="flex-1">
                  <div className="font-medium text-sm leading-snug">{article.title}</div>
                  <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                    <span>{article.source}</span>
                    <span>{article.time}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default function CryptoPage() {
  const [cryptoData, setCryptoData] = useState<CryptoPrice[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [viewMode, setViewMode] = useState<'card' | 'table'>('table');
  const [sortBy, setSortBy] = useState<'rank' | 'price' | 'change' | 'volume' | 'market_cap'>('rank');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [filterBy, setFilterBy] = useState<'all' | 'gainers' | 'losers'>('all');
  
  // Fixed watchlist for now - could be made dynamic later
  const watchlist = ['BTC', 'ETH', 'ADA'];

  useEffect(() => {
    const fetchCryptoData = async () => {
      try {
        if (!refreshing) setLoading(true);
        
        const data = await apiClient.getCryptoPrices();
        setCryptoData(data);
      } catch (error) {
        console.error('Error fetching crypto data:', error);
        // Keep existing state on error
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    };

    fetchCryptoData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchCryptoData, 30000);
    return () => clearInterval(interval);
  }, [refreshing]);

  const handleRefresh = () => {
    setRefreshing(true);
    // The useEffect will handle the actual refresh
  };

  // Filter and sort crypto data
  const sortedData = [...cryptoData]
    .filter(crypto => {
      if (filterBy === 'gainers') return crypto.change_percent_24h > 0;
      if (filterBy === 'losers') return crypto.change_percent_24h < 0;
      return true;
    })
    .sort((a, b) => {
      let aValue, bValue;
      
      switch (sortBy) {
        case 'rank':
          aValue = a.rank;
          bValue = b.rank;
          break;
        case 'price':
          aValue = a.price;
          bValue = b.price;
          break;
        case 'change':
          aValue = a.change_percent_24h;
          bValue = b.change_percent_24h;
          break;
        case 'volume':
          aValue = a.volume_24h;
          bValue = b.volume_24h;
          break;
        case 'market_cap':
          aValue = a.market_cap;
          bValue = b.market_cap;
          break;
        default:
          aValue = a.rank;
          bValue = b.rank;
      }

      if (sortOrder === 'asc') {
        return aValue - bValue;
      } else {
        return bValue - aValue;
      }
    });

  const handleSort = (column: typeof sortBy) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('asc');
    }
  };

  if (loading) {
    return (
      <RequireAuth>
        <PageLayout title="Crypto Market">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-400">Loading crypto data...</p>
            </div>
          </div>
        </PageLayout>
      </RequireAuth>
    );
  }

  return (
    <RequireAuth>
      <PageLayout
        title="🪙 Crypto Market Intelligence"
        subtitle="Real-time crypto prices and market analysis"
        theme="crypto"
        actions={
          <div className="flex items-center space-x-3">
            <Button
              onClick={handleRefresh}
              disabled={refreshing}
              variant="ghost"
              className="text-sm"
            >
              {refreshing ? '🔄' : '↻'} Refresh
            </Button>
            <Button
              onClick={() => setViewMode(viewMode === 'card' ? 'table' : 'card')}
              variant="ghost"
              className="text-sm"
            >
              {viewMode === 'card' ? '📋' : '🃏'} {viewMode === 'card' ? 'Table' : 'Cards'}
            </Button>
          </div>
        }
      >
        {/* Crypto Market Stats */}
        <CryptoStats cryptoData={cryptoData} />

        {/* Filters and Controls */}
        <div className="flex flex-wrap gap-4 mb-6">
          <div className="flex gap-2">
            <ThemedButton
              onClick={() => setFilterBy('all')}
              variant={filterBy === 'all' ? 'primary' : 'secondary'}
            >
              All
            </ThemedButton>
            <ThemedButton
              onClick={() => setFilterBy('gainers')}
              variant={filterBy === 'gainers' ? 'primary' : 'secondary'}
            >
              📈 Gainers
            </ThemedButton>
            <ThemedButton
              onClick={() => setFilterBy('losers')}
              variant={filterBy === 'losers' ? 'primary' : 'secondary'}
            >
              📉 Losers
            </ThemedButton>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          {/* Main crypto list */}
          <div className="xl:col-span-3">
            {viewMode === 'table' ? (
              <ThemedCard>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-700">
                        <th className="text-left p-4">
                          <Button 
                            variant="ghost" 
                            onClick={() => handleSort('rank')}
                            className="text-sm"
                          >
                            Rank {sortBy === 'rank' && (sortOrder === 'asc' ? '↑' : '↓')}
                          </Button>
                        </th>
                        <th className="text-right p-4">
                          <Button 
                            variant="ghost" 
                            onClick={() => handleSort('price')}
                            className="text-sm"
                          >
                            Price {sortBy === 'price' && (sortOrder === 'asc' ? '↑' : '↓')}
                          </Button>
                        </th>
                        <th className="text-right p-4">
                          <Button 
                            variant="ghost" 
                            onClick={() => handleSort('change')}
                            className="text-sm"
                          >
                            24h Change {sortBy === 'change' && (sortOrder === 'asc' ? '↑' : '↓')}
                          </Button>
                        </th>
                        <th className="text-right p-4">
                          <Button 
                            variant="ghost" 
                            onClick={() => handleSort('volume')}
                            className="text-sm"
                          >
                            24h Volume {sortBy === 'volume' && (sortOrder === 'asc' ? '↑' : '↓')}
                          </Button>
                        </th>
                        <th className="text-right p-4">
                          <Button 
                            variant="ghost" 
                            onClick={() => handleSort('market_cap')}
                            className="text-sm"
                          >
                            Market Cap {sortBy === 'market_cap' && (sortOrder === 'asc' ? '↑' : '↓')}
                          </Button>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedData.map(crypto => (
                        <CryptoCard
                          key={crypto.symbol}
                          crypto={crypto}
                          viewMode="table"
                        />
                      ))}
                    </tbody>
                  </table>
                </div>
              </ThemedCard>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {sortedData.map(crypto => (
                  <CryptoCard
                    key={crypto.symbol}
                    crypto={crypto}
                    viewMode="card"
                  />
                ))}
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <CryptoNews />
            
            {/* Watchlist */}
            <ThemedCard>
              <CardHeader>
                <CardTitle>Watchlist</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {watchlist.map(symbol => {
                    const crypto = cryptoData.find(c => c.symbol === symbol);
                    return crypto ? (
                      <div key={symbol} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded">
                        <div>
                          <div className="font-medium">{crypto.symbol}</div>
                          <div className="text-sm text-gray-500">{formatCurrency(crypto.price)}</div>
                        </div>
                        <div className={`text-sm ${getPriceColor(crypto.change_24h)}`}>
                          {crypto.change_24h >= 0 ? '+' : ''}{formatPercentage(crypto.change_percent_24h)}
                        </div>
                      </div>
                    ) : null;
                  })}
                </div>
              </CardContent>
            </ThemedCard>
          </div>
        </div>
      </PageLayout>
    </RequireAuth>
  );
}