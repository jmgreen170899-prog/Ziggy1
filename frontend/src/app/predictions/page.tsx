import { RequireAuth } from '@/routes/RequireAuth';
import { PredictionsHub } from '@/components/predictions/PredictionsHub';

export default function PredictionsPage() {
  return (
    <RequireAuth>
      <PredictionsHub />
    </RequireAuth>
  );
}

export const metadata = {
  title: 'AI Predictions | ZiggyClean',
  description: 'Advanced AI-powered trading predictions and market analysis',
};