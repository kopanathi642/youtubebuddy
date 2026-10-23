import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';

/**
 * Placeholder pages for footer links that have no content yet.
 * They render honestly ("not published yet") instead of returning a 404.
 * IMPORTANT: Terms, Privacy and Cookie policy must be replaced with real legal
 * text written/reviewed by the site owner before a production launch.
 */
const PAGES: Record<string, { title: string; blurb: string }> = {
  about: { title: 'About', blurb: 'Information about YouTube Buddy and its team.' },
  blog: { title: 'Blog', blurb: 'Product news and creator tips.' },
  careers: { title: 'Careers', blurb: 'Open roles at YouTube Buddy.' },
  contact: { title: 'Contact', blurb: 'Ways to reach the YouTube Buddy team.' },
  docs: { title: 'Documentation', blurb: 'Guides for using YouTube Buddy.' },
  'api-docs': { title: 'API Reference', blurb: 'Reference documentation for the YouTube Buddy API.' },
  changelog: { title: 'Changelog', blurb: 'A history of product updates.' },
  status: { title: 'Status', blurb: 'Live service status.' },
  privacy: { title: 'Privacy Policy', blurb: 'How your data is collected and used.' },
  terms: { title: 'Terms of Service', blurb: 'The terms that govern use of YouTube Buddy.' },
  cookies: { title: 'Cookie Policy', blurb: 'How cookies and local storage are used.' },
};

export const dynamicParams = false;

export function generateStaticParams() {
  return Object.keys(PAGES).map((page) => ({ page }));
}

export default async function InfoPage({ params }: { params: Promise<{ page: string }> }) {
  const { page } = await params;
  const content = PAGES[page];
  if (!content) notFound();

  return (
    <div className="min-h-screen bg-bg-primary">
      <Navbar />
      <main className="max-w-2xl mx-auto px-6 pt-32 pb-24 text-center">
        <h1 className="font-display text-4xl font-bold text-white mb-4">{content.title}</h1>
        <p className="text-white/60 mb-2">{content.blurb}</p>
        <p className="text-white/40 text-sm mb-10">This page hasn&apos;t been published yet. Please check back soon.</p>
        <Link
          href="/"
          className="inline-flex items-center px-5 py-2.5 rounded-xl border border-white/10 text-white/80 hover:bg-white/5 transition-colors text-sm"
        >
          Back to home
        </Link>
      </main>
      <Footer />
    </div>
  );
}
