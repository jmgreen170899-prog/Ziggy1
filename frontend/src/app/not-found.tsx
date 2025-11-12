import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center">
          <CardTitle className="flex items-center justify-center space-x-2 text-gray-800 dark:text-gray-200">
            <span className="text-3xl">🔍</span>
            <span>Page Not Found</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-center">
          <p className="text-gray-600 dark:text-gray-400">
            The page you&apos;re looking for doesn&apos;t exist or has been moved.
          </p>
          
          <div className="flex flex-col space-y-3">
            <Link href="/">
              <Button className="w-full">
                Go to Dashboard
              </Button>
            </Link>
            <Link href="/market">
              <Button variant="outline" className="w-full">
                View Markets
              </Button>
            </Link>
            <Link href="/portfolio">
              <Button variant="ghost" className="w-full">
                Portfolio
              </Button>
            </Link>
          </div>

          <div className="text-xs text-gray-500 dark:text-gray-400">
            Error 404 - Page not found
          </div>
        </CardContent>
      </Card>
    </div>
  );
}