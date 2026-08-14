import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Analytics } from "@vercel/analytics/next";
import ThemeSync from "@/components/ThemeSync";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { CommandPalette, MobileBottomNav } from "@/components/layout";
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
  title: "RailYatra AI — The AI Operating System for Travel Decisions",
  description: "Advanced AI-powered railway travel intelligence platform offering predictions, routing recommendations, and smart travel assistants.",
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
        <MobileBottomNav />
        <Analytics />
      </body>
    </html>
  );
}
