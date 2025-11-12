import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/ui/Sidebar";
import { ThemeProvider } from "@/providers/ThemeProvider";
import { IntroGate } from "@/features/intro";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { KeyboardShortcuts } from "@/components/ui/KeyboardShortcuts";
import { ToastProvider } from "@/components/ui/Toast";

const inter = Inter({ subsets: ["latin"] });

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
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
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
