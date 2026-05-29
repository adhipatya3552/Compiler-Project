import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import "./globals.css";

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "App Compiler — Natural Language → App Config",
  description: "Multi-stage pipeline that converts natural language into structured, executable app configurations.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${jetbrains.variable} font-mono antialiased`}>{children}</body>
    </html>
  );
}