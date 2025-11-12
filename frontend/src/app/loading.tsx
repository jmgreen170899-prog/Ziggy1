import { LoadingState } from '@/components/ui/Loading';

export default function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <LoadingState 
        message="Loading ZiggyAI Dashboard..." 
        size="lg"
      />
    </div>
  );
}