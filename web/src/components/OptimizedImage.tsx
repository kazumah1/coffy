'use client'

import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { useInView } from 'react-intersection-observer'

interface OptimizedImageProps {
  src: string
  alt: string
  className?: string
  width?: number
  height?: number
  priority?: boolean
  quality?: number
  placeholder?: 'blur' | 'empty'
  blurDataURL?: string
  sizes?: string
  onLoad?: () => void
  onError?: () => void
}

const OptimizedImage = ({
  src,
  alt,
  className = '',
  width,
  height,
  priority = false,
  quality = 85,
  placeholder = 'empty',
  blurDataURL,
  sizes,
  onLoad,
  onError
}: OptimizedImageProps) => {
  const [isLoaded, setIsLoaded] = useState(false)
  const [hasError, setHasError] = useState(false)
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
    skip: priority
  })

  const handleLoad = () => {
    setIsLoaded(true)
    onLoad?.()
  }

  const handleError = () => {
    setHasError(true)
    onError?.()
  }

  const getOptimizedSrc = (originalSrc: string, format?: 'webp' | 'avif') => {
    if (format) {
      const extension = originalSrc.split('.').pop()
      return originalSrc.replace(`.${extension}`, `.${format}`)
    }
    return originalSrc
  }

  const shouldLoad = priority || inView

  if (hasError) {
    return (
      <div
        className={`bg-coffy-beige/30 flex items-center justify-center ${className}`}
        style={{ width, height }}
      >
        <span className="text-coffy-brown/50 text-sm">Failed to load image</span>
      </div>
    )
  }

  return (
    <div ref={ref} className={`relative overflow-hidden ${className}`}>
      {placeholder === 'blur' && blurDataURL && !isLoaded && shouldLoad && (
        <img
          src={blurDataURL}
          alt=""
          className="absolute inset-0 w-full h-full object-cover filter blur-sm scale-110"
          aria-hidden="true"
        />
      )}
      {!isLoaded && shouldLoad && (
        <div className="absolute inset-0 bg-gradient-to-r from-coffy-cream/50 to-coffy-beige/50 animate-pulse" />
      )}

      {shouldLoad && (
        <motion.picture
          initial={{ opacity: 0, scale: 1.1 }}
          animate={isLoaded ? { opacity: 1, scale: 1 } : {}}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          <source
            srcSet={`${getOptimizedSrc(src, 'webp')}`}
            type="image/webp"
            sizes={sizes}
          />
          <source
            srcSet={`${getOptimizedSrc(src, 'avif')}`}
            type="image/avif"
            sizes={sizes}
          />
          <img
            src={src}
            alt={alt}
            width={width}
            height={height}
            className="w-full h-full object-cover"
            loading={priority ? 'eager' : 'lazy'}
            onLoad={handleLoad}
            onError={handleError}
            sizes={sizes}
          />
        </motion.picture>
      )}
    </div>
  )
}

export default OptimizedImage
