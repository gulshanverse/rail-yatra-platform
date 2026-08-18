import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Analytics } from "@vercel/analytics/next";
import ThemeSync from "@/components/ThemeSync";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { CommandPalette } from "@/components/layout";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RailYatra — Smarter journeys, from search to station",
  description: "RailYatra is the premium AI-powered railway travel platform for discovering routes, comparing trains, planning journeys, and staying informed on the move.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full bg-background text-foreground">
        <ThemeSync />
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
        <CommandPalette />
        <Analytics />
      </body>
    </html>
  );
}
