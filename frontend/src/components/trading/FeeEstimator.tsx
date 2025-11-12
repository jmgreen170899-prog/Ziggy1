'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface FeeEstimate {
  symbol: string;
  quantity: number;
  price: number;
  notionalValue: number;
  commissionBps: number;
  commissionAmount: number;
  feeCapPerOrder: number;
  finalCommission: number;
  effectiveBps: number;
  mode: 'NOTIONAL' | 'PNL_SHARE' | 'OFF';
  pnlShareRate?: number;
  highWaterMark?: number;
  monthlyCapReached?: boolean;
}

interface FeeEstimatorProps {
  symbol: string;
  quantity: number;
  price: number;
  side: 'BUY' | 'SELL';
  venue?: string;
  onFeeChange?: (fee: FeeEstimate) => void;
  showBreakdown?: boolean;
}

// Environment variables (would come from backend/config)
const FEE_CONFIG = {
  EXEC_FEE_MODE: process.env.NEXT_PUBLIC_EXEC_FEE_MODE || 'NOTIONAL',
  PERCENT_FEE_BPS: parseFloat(process.env.NEXT_PUBLIC_PERCENT_FEE_BPS || '10'), // 10 bps = 0.10%
  FEE_CAP_PER_ORDER: parseFloat(process.env.NEXT_PUBLIC_FEE_CAP_PER_ORDER || '5.00'),
  PERCENT_PNL_SHARE: parseFloat(process.env.NEXT_PUBLIC_PERCENT_PNL_SHARE || '10'), // 10%
  PNL_SHARE_MONTHLY_CAP: parseFloat(process.env.NEXT_PUBLIC_PNL_SHARE_MONTHLY_CAP || '99.00'),
  HIGH_WATER_MARK: process.env.NEXT_PUBLIC_HIGH_WATER_MARK === 'ON',
  EXEC_FEE_PAPER: parseFloat(process.env.NEXT_PUBLIC_EXEC_FEE_PAPER || '0'),
};

export function FeeEstimator({ 
  symbol, 
  quantity, 
  price, 
  side, 
  venue = 'IBKR',
  onFeeChange,
  showBreakdown = true 
}: FeeEstimatorProps) {
  const [feeEstimate, setFeeEstimate] = useState<FeeEstimate | null>(null);
  const [paperMode, setPaperMode] = useState(false);

  useEffect(() => {
    const notionalValue = quantity * price;
    
    if (paperMode) {
      const estimate: FeeEstimate = {
        symbol,
        quantity,
        price,
        notionalValue,
        commissionBps: 0,
        commissionAmount: 0,
        feeCapPerOrder: 0,
        finalCommission: 0,
        effectiveBps: 0,
        mode: 'OFF'
      };
      setFeeEstimate(estimate);
      onFeeChange?.(estimate);
      return;
    }

    let estimate: FeeEstimate;

    if (FEE_CONFIG.EXEC_FEE_MODE === 'NOTIONAL') {
      const commissionAmount = (notionalValue * FEE_CONFIG.PERCENT_FEE_BPS) / 10000;
      const finalCommission = Math.min(commissionAmount, FEE_CONFIG.FEE_CAP_PER_ORDER);
      const effectiveBps = (finalCommission / notionalValue) * 10000;

      estimate = {
        symbol,
        quantity,
        price,
        notionalValue,
        commissionBps: FEE_CONFIG.PERCENT_FEE_BPS,
        commissionAmount,
        feeCapPerOrder: FEE_CONFIG.FEE_CAP_PER_ORDER,
        finalCommission,
        effectiveBps,
        mode: 'NOTIONAL'
      };
    } else if (FEE_CONFIG.EXEC_FEE_MODE === 'PNL_SHARE') {
      // For PNL share, we show potential fee only (actual depends on realized gains)
      estimate = {
        symbol,
        quantity,
        price,
        notionalValue,
        commissionBps: 0,
        commissionAmount: 0,
        feeCapPerOrder: 0,
        finalCommission: 0, // Only on realized gains
        effectiveBps: 0,
        mode: 'PNL_SHARE',
        pnlShareRate: FEE_CONFIG.PERCENT_PNL_SHARE,
        highWaterMark: FEE_CONFIG.HIGH_WATER_MARK ? 1000 : undefined, // Mock value
        monthlyCapReached: false
      };
    } else {
      estimate = {
        symbol,
        quantity,
        price,
        notionalValue,
        commissionBps: 0,
        commissionAmount: 0,
        feeCapPerOrder: 0,
        finalCommission: 0,
        effectiveBps: 0,
        mode: 'OFF'
      };
    }

    setFeeEstimate(estimate);
    onFeeChange?.(estimate);
  }, [symbol, quantity, price, side, venue, paperMode, onFeeChange]);

  if (!feeEstimate) return null;

  return (
    <Card className="border-amber-200 dark:border-amber-800 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-amber-800 dark:text-amber-200">
          <div className="flex items-center space-x-2">
            <span>💰</span>
            <span className="text-lg">Fee Estimate</span>
            <span className="text-xs bg-amber-200 dark:bg-amber-800 px-2 py-1 rounded-full">
              {feeEstimate.mode === 'OFF' ? 'Paper Trading' : feeEstimate.mode}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              onClick={() => setPaperMode(!paperMode)}
              size="sm"
              variant={paperMode ? "primary" : "ghost"}
              className="text-xs"
            >
              📝 Paper Mode
            </Button>
            <Button size="sm" variant="ghost" className="text-xs">
              ⚙️ Settings
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Trade Summary */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-amber-700 dark:text-amber-300">Order:</span>
              <span className="ml-2 font-medium">{side} {quantity} {symbol} @ ${price.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-amber-700 dark:text-amber-300">Notional:</span>
              <span className="ml-2 font-medium">${feeEstimate.notionalValue.toLocaleString()}</span>
            </div>
          </div>

          {/* Fee Breakdown */}
          {showBreakdown && (
            <div className="border border-amber-200 dark:border-amber-700 rounded-lg p-3 bg-white/50 dark:bg-black/20">
              <div className="text-sm font-medium mb-2 text-amber-800 dark:text-amber-200">Fee Breakdown</div>
              
              {feeEstimate.mode === 'NOTIONAL' && (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Base Commission ({feeEstimate.commissionBps} bps):</span>
                    <span>${feeEstimate.commissionAmount.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Per-Order Cap:</span>
                    <span>${feeEstimate.feeCapPerOrder.toFixed(2)}</span>
                  </div>
                  <hr className="border-amber-200 dark:border-amber-700" />
                  <div className="flex justify-between font-medium">
                    <span>Final Commission:</span>
                    <span className="text-red-600 dark:text-red-400">${feeEstimate.finalCommission.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-xs text-amber-600 dark:text-amber-400">
                    <span>Effective Rate:</span>
                    <span>{feeEstimate.effectiveBps.toFixed(1)} bps</span>
                  </div>
                </div>
              )}

              {feeEstimate.mode === 'PNL_SHARE' && (
                <div className="space-y-2 text-sm">
                  <div className="text-amber-700 dark:text-amber-300">
                    📊 P&L Share Model Active
                  </div>
                  <div className="space-y-1">
                    <div>• {feeEstimate.pnlShareRate}% of realized net gains</div>
                    <div>• Monthly cap: ${FEE_CONFIG.PNL_SHARE_MONTHLY_CAP}</div>
                    {FEE_CONFIG.HIGH_WATER_MARK && (
                      <div>• High-water mark protection enabled</div>
                    )}
                    <div className="text-xs text-amber-600 dark:text-amber-400 mt-2">
                      No upfront commission. Fee only applies to profitable closed positions.
                    </div>
                  </div>
                </div>
              )}

              {feeEstimate.mode === 'OFF' && (
                <div className="text-sm text-green-700 dark:text-green-300">
                  📝 Paper trading mode - No execution fees
                </div>
              )}
            </div>
          )}

          {/* Net Impact */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
            <div className="text-sm font-medium mb-2 text-blue-800 dark:text-blue-200">Net Impact Analysis</div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-blue-700 dark:text-blue-300">Break-even move:</span>
                <span className="ml-2 font-medium">
                  {feeEstimate.mode === 'OFF' ? '$0.00' : `$${(feeEstimate.finalCommission / quantity).toFixed(2)}`}
                </span>
              </div>
              <div>
                <span className="text-blue-700 dark:text-blue-300">Total cost basis:</span>
                <span className="ml-2 font-medium">
                  ${(feeEstimate.notionalValue + feeEstimate.finalCommission).toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* Transparency Notice */}
          <div className="text-xs text-amber-600 dark:text-amber-400 bg-amber-100/50 dark:bg-amber-900/20 p-2 rounded">
            <div className="flex items-start space-x-1">
              <span>⚠️</span>
              <div>
                <div className="font-medium">Transparency Notice:</div>
                <div>
                  • Third-party broker/exchange fees may apply separately
                  • Venue routing may affect final execution costs
                  • All backtests and performance metrics include these estimated fees
                  • Fee optimization suggestions available in Coach Mode
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-2">
            <Button size="sm" variant="ghost" className="text-xs">
              📖 Fee Documentation
            </Button>
            <div className="flex space-x-2">
              <Button size="sm" variant="ghost" className="text-xs">
                📊 Historical Fees
              </Button>
              <Button size="sm" variant="ghost" className="text-xs">
                🔧 Optimize Settings
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Export types for use in other components
export type { FeeEstimate, FeeEstimatorProps };