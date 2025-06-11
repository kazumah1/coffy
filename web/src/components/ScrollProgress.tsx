'use client'

import { useEffect, useState } from 'react'

const ScrollProgress = () => {
  const [scrollProgress, setScrollProgress] = useState(0)

  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY
      const docHeight = document.documentElement.scrollHeight - window.innerHeight
      const scrollPercent = Math.min(scrollTop / docHeight, 1)
      setScrollProgress(scrollPercent)
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    handleScroll()

    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div
      className="scroll-indicator transition-transform duration-75 ease-out"
      style={{
        transform: `scaleX(${scrollProgress})`,
        transformOrigin: 'left'
      }}
    />
  )
}

export default ScrollProgress
