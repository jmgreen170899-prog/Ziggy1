/**
 * Paper Trading Status Page
 * 
 * Comprehensive dashboard for monitoring autonomous paper trading system
 */

import PaperStatus from '@/features/paper/PaperStatus';

export default function PaperStatusPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <PaperStatus />
    </div>
  );
}