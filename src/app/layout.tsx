import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "VeriCode - Live Documentation Verifier",
  description: "Fight documentation rot with VeriCode - the tool that verifies if code snippets from tutorials still work with the latest dependencies.",
  keywords: ["VeriCode", "documentation", "code verification", "tutorial", "development", "programming"],
  authors: [{ name: "VeriCode Team" }],
  openGraph: {
    title: "VeriCode - Live Documentation Verifier",
    description: "Fight documentation rot with real-time code verification",
    url: "https://vericode.app",
    siteName: "VeriCode",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "VeriCode - Live Documentation Verifier",
    description: "Fight documentation rot with real-time code verification",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        {children}
        <Toaster />
      </body>
    </html>
  );
}
