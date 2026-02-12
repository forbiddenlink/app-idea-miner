import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'

interface LazyImageProps {
  src: string
  alt: string
  className?: string
  blurDataURL?: string
  onLoad?: () => void
  width?: number
  height?: number
}

/**
 * LazyImage Component
 *
 * Implements lazy loading with blur placeholder using IntersectionObserver.
 * Only loads images when they enter the viewport.
 *
 * Features:
 * - Blur-up placeholder effect
 * - Fade-in animation on load
 * - IntersectionObserver for performance
 * - Fallback for browsers without IntersectionObserver
 */
export function LazyImage({
  src,
  alt,
  className = '',
  blurDataURL,
  onLoad,
  width,
  height,
}: LazyImageProps) {
  const [isLoaded, setIsLoaded] = useState(false)
  const [isInView, setIsInView] = useState(false)
  const imgRef = useRef<HTMLImageElement>(null)

  useEffect(() => {
    // Check if IntersectionObserver is supported
    if (!('IntersectionObserver' in window)) {
      // Fallback: load immediately
      setIsInView(true)
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true)
            observer.disconnect()
          }
        })
      },
      {
        rootMargin: '50px', // Start loading 50px before entering viewport
        threshold: 0.01,
      }
    )

    if (imgRef.current) {
      observer.observe(imgRef.current)
    }

    return () => {
      observer.disconnect()
    }
  }, [])

  const handleLoad = () => {
    setIsLoaded(true)
    onLoad?.()
  }

  return (
    <div
      className={`relative overflow-hidden ${className}`}
      style={{ width, height }}
    >
      {/* Blur placeholder */}
      {blurDataURL && !isLoaded && (
        <img
          src={blurDataURL}
          alt=""
          aria-hidden="true"
          className="absolute inset-0 w-full h-full object-cover blur-xl scale-110"
        />
      )}

      {/* Skeleton loader if no blur placeholder */}
      {!blurDataURL && !isLoaded && (
        <div className="absolute inset-0 bg-slate-800 animate-pulse" />
      )}

      {/* Actual image */}
      <motion.img
        ref={imgRef}
        src={isInView ? src : undefined}
        alt={alt}
        className={`w-full h-full object-cover transition-opacity duration-300 ${
          isLoaded ? 'opacity-100' : 'opacity-0'
        }`}
        onLoad={handleLoad}
        loading="lazy"
        initial={{ opacity: 0 }}
        animate={{ opacity: isLoaded ? 1 : 0 }}
        transition={{ duration: 0.3 }}
      />
    </div>
  )
}
