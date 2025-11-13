import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { Sidebar } from "@/components/ui/Sidebar";
import { ThemeProvider } from "@/providers/ThemeProvider";
import { IntroGate } from "@/features/intro";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { KeyboardShortcuts } from "@/components/ui/KeyboardShortcuts";
import { ToastProvider } from "@/components/ui/Toast";

const inter = localFont({
  src: [
    {
      path: '../../public/fonts/inter/Inter-Regular.woff2',
      weight: '400',
      style: 'normal',
    },
    {
      path: '../../public/fonts/inter/Inter-Medium.woff2',
      weight: '500',
      style: 'normal',
    },
    {
      path: '../../public/fonts/inter/Inter-SemiBold.woff2',
      weight: '600',
      style: 'normal',
    },
    {
      path: '../../public/fonts/inter/Inter-Bold.woff2',
      weight: '700',
      style: 'normal',
    },
  ],
  variable: '--font-inter',
  display: 'swap',
});

export const metadata: Metadata = {
  title: "ZiggyClean - Financial Trading Platform",
  description: "Advanced financial trading and market analysis platform with AI-powered insights",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className={inter.variable}>
      <body>
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        <ErrorBoundary>
          <ThemeProvider>
            <ToastProvider>
              <AuthGuard>
                <IntroGate appVersion="1.0.0" theme="light">
                  <Sidebar>
                    <main id="main-content">
                      {children}
                    </main>
                  </Sidebar>
                  <KeyboardShortcuts />
                </IntroGate>
              </AuthGuard>
            </ToastProvider>
          </ThemeProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
