import { useState, useEffect } from 'react';
import { isDemoMode } from '@/config/demo';

/**
 * Demo data types available from backend
 */
export type DemoDataType = 'market' | 'portfolio' | 'signals' | 'news' | 'backtest' | 'screener' | 'cognitive';

/**
 * Hook to fetch demo data from backend when in demo mode
 */
export function useDemoData<T = any>(
  dataType: DemoDataType,
  params?: Record<string, any>
): { data: T | null; loading: boolean; error: Error | null } {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!isDemoMode()) {
      return;
    }

    const fetchDemoData = async () => {
      setLoading(true);
      try {
        const queryString = params
          ? '?' + new URLSearchParams(params).toString()
          : '';
        const response = await fetch(`/demo/data/${dataType}${queryString}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch demo data: ${response.statusText}`);
        }

        const result = await response.json();
        setData(result);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchDemoData();
  }, [dataType, JSON.stringify(params)]);

  return { data, loading, error };
}

/**
 * Higher-order component that provides demo data fallback
 */
export function withDemoFallback<P extends object>(
  Component: React.ComponentType<P>,
  demoDataType: DemoDataType,
  demoParams?: Record<string, any>
) {
  return function DemoFallbackComponent(props: P) {
    const { data: demoData, loading } = useDemoData(demoDataType, demoParams);

    if (isDemoMode() && loading) {
      return <div>Loading demo data...</div>;
    }

    const enhancedProps = isDemoMode() && demoData
      ? { ...props, demoData }
      : props;

    return <Component {...enhancedProps} />;
  };
}

/**
 * Determines if demo data should be used based on current mode
 */
export function shouldUseDemoData(): boolean {
  return isDemoMode();
}

/**
 * Fetches specific demo data programmatically
 */
export async function getDemoDataFor<T = any>(
  dataType: DemoDataType,
  params?: Record<string, any>
): Promise<T | null> {
  if (!isDemoMode()) {
    return null;
  }

  try {
    const queryString = params
      ? '?' + new URLSearchParams(params).toString()
      : '';
    const response = await fetch(`/demo/data/${dataType}${queryString}`);
    
    if (!response.ok) {
      console.error(`Failed to fetch demo data: ${response.statusText}`);
      return null;
    }

    return await response.json();
  } catch (err) {
    console.error('Error fetching demo data:', err);
    return null;
  }
}

/**
 * Check if a specific feature is disabled in demo mode
 */
export function isDemoFeatureDisabled(feature: string): boolean {
  if (!isDemoMode()) {
    return false;
  }

  const disabledFeatures = [
    'real_trading',
    'data_ingestion',
    'system_modifications',
    'user_management',
    'api_key_generation',
  ];

  return disabledFeatures.includes(feature);
}

/**
 * Get demo mode warning message for a disabled feature
 */
export function getDemoWarning(feature: string): string {
  const warnings: Record<string, string> = {
    real_trading: 'Real trading is disabled in demo mode. Use paper trading instead.',
    data_ingestion: 'Data ingestion is disabled in demo mode. Using cached demo data.',
    system_modifications: 'System modifications are disabled in demo mode.',
    user_management: 'User management is disabled in demo mode.',
    api_key_generation: 'API key generation is disabled in demo mode.',
  };

  return warnings[feature] || 'This feature is disabled in demo mode.';
}
