import Navigation from '@/components/Navigation'
import HeroSection from '@/components/HeroSection'
import FeaturesSection from '@/components/FeaturesSection'
import WaitlistSection from '@/components/WaitlistSection'

export default function Home() {
  return (
    <main className="overflow-x-hidden">
      <Navigation />
      <HeroSection />
      <FeaturesSection />
      <WaitlistSection />
    </main>
  )
}
