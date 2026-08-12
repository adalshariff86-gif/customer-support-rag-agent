import React from 'react';
import { Navbar } from '../common/Navbar';
import { HeroSection } from './HeroSection';
import { HowItWorks } from './HowItWorks';
import { TechStack } from './TechStack';
import { DevFeatures } from './DevFeatures';
import { LiveDemoSection } from './LiveDemoSection';
import { Footer } from '../common/Footer';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-white dark:bg-[#0A0C10] text-zinc-900 dark:text-slate-100 selection:bg-indigo-500 selection:text-white transition-colors duration-200">
      <Navbar />
      <main>
        <HeroSection />
        <HowItWorks />
        <TechStack />
        <DevFeatures />
        <LiveDemoSection />
      </main>
      <Footer />
    </div>
  );
};
