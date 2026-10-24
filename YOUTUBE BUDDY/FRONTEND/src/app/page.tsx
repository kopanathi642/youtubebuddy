import { RememberedEntry } from '@/components/studios/RememberedEntry';
import Link from 'next/link';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';
import { HeroSection } from '@/components/home/HeroSection';
import { FeaturesSection } from '@/components/home/FeaturesSection';
import { PricingPreview } from '@/components/home/PricingPreview';

export default function HomePage() {
  return (
    <main className="min-h-screen bg-bg-primary">
      <RememberedEntry />
      <Navbar />
      <div className="border-b border-purple-400/20 bg-purple-500/10 p-4 text-center text-sm"><Link href="/studios/" className="text-purple-200 hover:text-white">Explore all 30 creative workspaces →</Link></div>
      <HeroSection />
      <FeaturesSection />
      <PricingPreview />
      <Footer />
    </main>
  );
}
