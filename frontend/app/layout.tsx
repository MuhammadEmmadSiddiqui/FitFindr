import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'FitFindr — AI Resume Screening',
  description: 'AI-powered resume screening powered by BERT and LangGraph',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
