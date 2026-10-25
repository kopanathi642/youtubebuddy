import type { Metadata } from 'next';
import { Inter, Space_Grotesk, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import './creator.css';
import { AuthProvider } from '@/context/AuthContext';
import { QueryProvider } from '@/context/QueryProvider';
import { Toaster } from 'react-hot-toast';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-space-grotesk',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: {
    default: 'YouTube Buddy X — Creative Studio',
    template: '%s | YouTube Buddy X',
  },
  description:
    'Create and edit locally, organize creative projects and analyze authorized or imported YouTube reports. AI generation requires a configured processing engine.',
  keywords: [
    'YouTube automation',
    'AI creator tools',
    'shorts generator',
    'video AI',
    'content creation',
    'YouTube growth',
    'AI agents',
    'viral shorts',
  ],
  authors: [{ name: 'YouTube Buddy X' }],
  creator: 'YouTube Buddy X',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: process.env.NEXT_PUBLIC_APP_URL,
    title: 'YouTube Buddy — AI Creator Platform',
    description:
      'A creative workspace for local editing, story planning and evidence-led YouTube reporting.',
    siteName: 'YouTube Buddy',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'YouTube Buddy — AI Creator Platform',
    description: 'Creative tools and evidence-led channel reporting.',
    creator: '@youtubebuddy',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  icons: {
    icon: {url:'/favicon.svg',type:'image/svg+xml'},
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable}`}
      suppressHydrationWarning
    >
      <body className="bg-bg-primary text-white antialiased" suppressHydrationWarning>
        <QueryProvider>
          <AuthProvider>
            {children}
            <Toaster
              position="bottom-right"
              toastOptions={{
                style: {
                  background: 'rgba(13, 13, 23, 0.95)',
                  backdropFilter: 'blur(12px)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  color: '#ffffff',
                  borderRadius: '12px',
                  fontSize: '14px',
                },
                success: {
                  iconTheme: {
                    primary: '#a3e635',
                    secondary: '#000000',
                  },
                },
                error: {
                  iconTheme: {
                    primary: '#f87171',
                    secondary: '#000000',
                  },
                },
              }}
            />
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
