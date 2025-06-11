'use client'

import { motion } from 'framer-motion'
import { useInView } from 'react-intersection-observer'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faPlay, faArrowDown, faCoffee, faUsers } from '@fortawesome/free-solid-svg-icons'
import TryoutModal from './TryoutModal'

const HeroSection = () => {
  const { ref, inView } = useInView({
    threshold: 0.1,
    triggerOnce: true
  })

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2,
        delayChildren: 0.1
      }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.8,
        ease: "easeOut"
      }
    }
  }

  const floatVariants = {
    animate: {
      y: [-10, 10, -10],
      transition: {
        duration: 4,
        repeat: Number.POSITIVE_INFINITY,
        ease: "easeInOut"
      }
    }
  }

  return (
    <section
      ref={ref}
      id="home"
      className="min-h-screen bg-gradient-to-br from-[#FFF8DC] via-[#F7F5F3] to-[#FAF0E6] overflow-hidden relative flex items-center"
    >
      {/* Enhanced Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,rgba(139,69,19,0.02)_1px,transparent_0)] bg-[length:40px_40px]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_1200px_800px_at_80%_20%,rgba(139,69,19,0.03)_0%,transparent_50%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_800px_600px_at_20%_80%,rgba(210,180,140,0.02)_0%,transparent_50%)]" />
      </div>

      <div className="container mx-auto px-6 py-16 relative z-10">
        <motion.div
          className="flex flex-col lg:flex-row items-center justify-between gap-16"
          variants={containerVariants}
          initial="hidden"
          animate={inView ? "visible" : "hidden"}
        >
          {/* Left Content */}
          <div className="lg:w-1/2 text-center lg:text-left">
            <motion.div
              variants={itemVariants}
              className="mb-6"
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/70 backdrop-blur-sm rounded-full border border-[#8B4513]/10 mb-8 shadow-sm">
                <FontAwesomeIcon icon={faCoffee} className="text-[#8B4513] text-sm" />
                <span className="text-[#8B4513] font-medium text-sm">Meet Coffy, Your Coffee Companion</span>
              </div>
            </motion.div>

            <motion.h1
              variants={itemVariants}
              className="text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-bold leading-tight mb-8"
            >
              Plan Together,{' '}
              <br />
              <span className="bg-gradient-to-r from-[#8B4513] via-[#A0522D] to-[#6B3A1A] bg-clip-text text-transparent">
                Coffee
              </span>{' '}
              Better
            </motion.h1>

            <motion.p
              variants={itemVariants}
              className="text-lg md:text-xl lg:text-2xl text-[#6B3A1A] mb-10 leading-relaxed max-w-2xl mx-auto lg:mx-0"
            >
              Meet Coffy, your AI companion who helps you coordinate
              coffee dates, group hangouts, and social adventures with effortless ease.
            </motion.p>

            <motion.div
              variants={itemVariants}
              className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start mb-12"
            >
              <button className="group relative overflow-hidden bg-gradient-to-r from-[#8B4513] to-[#6B3A1A] text-white px-8 py-4 rounded-full font-semibold shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <span className="relative z-10 flex items-center gap-2">
                  <FontAwesomeIcon icon={faUsers} />
                  Join the Waitlist
                </span>
                <div className="absolute inset-0 bg-gradient-to-r from-[#6B3A1A] to-[#4A2612] opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              </button>

              <TryoutModal>
                <button className="group relative bg-white/70 backdrop-blur-sm border-2 border-[#8B4513] text-[#8B4513] px-8 py-4 rounded-full font-semibold hover:bg-[#8B4513] hover:text-white transition-all duration-300 hover:-translate-y-1">
                  <span className="flex items-center gap-2">
                    <FontAwesomeIcon icon={faPlay} />
                    Try it out
                  </span>
                </button>
              </TryoutModal>
            </motion.div>
            <motion.div
              variants={itemVariants}
              className="flex flex-col sm:flex-row gap-6 justify-center lg:justify-start text-sm text-[#6B3A1A]"
            >
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span>AI-Powered Planning</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span>Natural Conversations</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span>Group Coordination</span>
              </div>
            </motion.div>
          </div>
          <motion.div
            className="lg:w-1/2 flex justify-center"
            variants={itemVariants}
          >
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-[#8B4513]/10 to-[#6B3A1A]/10 rounded-full blur-3xl scale-150" />

              <motion.div
                variants={floatVariants}
                animate="animate"
                className="relative"
              >
                <div className="relative">
                  <img
                    src="/image.png"
                    alt="Coffy the Coffee Mascot"
                    className="w-72 h-72 md:w-96 md:h-96 object-contain drop-shadow-2xl"
                  />
                  <motion.div
                    className="absolute -top-4 -right-4 bg-white/80 backdrop-blur-sm rounded-full p-3 shadow-lg"
                    animate={{
                      y: [-5, 5, -5],
                      rotate: [0, 5, 0, -5, 0]
                    }}
                    transition={{
                      duration: 3,
                      repeat: Number.POSITIVE_INFINITY,
                      ease: "easeInOut",
                      delay: 0.5
                    }}
                  >
                    <FontAwesomeIcon icon={faCoffee} className="text-[#8B4513] text-lg" />
                  </motion.div>

                  <motion.div
                    className="absolute -bottom-4 -left-4 bg-white/80 backdrop-blur-sm rounded-full p-3 shadow-lg"
                    animate={{
                      y: [5, -5, 5],
                      rotate: [0, -5, 0, 5, 0]
                    }}
                    transition={{
                      duration: 3.5,
                      repeat: Number.POSITIVE_INFINITY,
                      ease: "easeInOut",
                      delay: 1
                    }}
                  >
                    <FontAwesomeIcon icon={faUsers} className="text-[#8B4513] text-lg" />
                  </motion.div>
                </div>
              </motion.div>
            </div>
          </motion.div>
        </motion.div>
        <motion.div
          className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.6, delay: 1.5 }}
        >
        </motion.div>
      </div>
    </section>
  )
}

export default HeroSection
