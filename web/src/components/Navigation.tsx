'use client'

import { useState, useEffect } from 'react'

const Navigation = () => {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const navItems = [
    { href: '#home', label: 'Home' },
    { href: '#features', label: 'Features' },
    { href: '#waitlist', label: 'Join Waitlist' },
  ]

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 fade-in ${
        scrolled
          ? 'glass-morphism py-4 shadow-lg'
          : 'bg-transparent py-6'
      }`}
    >
      <div className="container mx-auto px-6 flex items-center justify-between">
        <div className="flex items-center space-x-3 hover:scale-105 transition-transform duration-200">
          <img
        src="/logo.png"
        alt="Coffy Logo"
        className="w-10 h-10"
          />
          <span className="font-bold text-2xl hero-text">Coffy</span>
        </div>

        <div className="hidden md:flex items-center space-x-8">
          {navItems.map((item, index) => (
            <a
              key={item.href}
              href={item.href}
              className={`text-coffy-brown hover:text-coffy-coffee transition-all duration-200 font-medium hover:scale-105 fade-in-delay-${Math.min(index + 1, 3)}`}
            >
              {item.label}
            </a>
          ))}
        </div>

        <button className="coffee-button text-coffy-cream px-6 py-3 rounded-full font-semibold shadow-md hover:shadow-lg hover:scale-105 transition-all duration-200 fade-in-delay-2">
          Get Started
        </button>
      </div>
    </nav>
  )
}

export default Navigation
