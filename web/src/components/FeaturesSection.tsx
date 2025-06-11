'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useInView } from 'react-intersection-observer'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faUsers,
  faCalendarAlt,
  faComments,
  faMapMarkerAlt,
  faLink,
  faRobot
} from '@fortawesome/free-solid-svg-icons'

const FeaturesSection = () => {
  const { ref, inView } = useInView({
    threshold: 0.1,
    triggerOnce: true
  })

  const features = [
    {
      id: "group-coordination",
      icon: faUsers,
      title: "Group Coordination",
      description: "Effortlessly manage friend groups, schedule hangouts, and keep everyone in the loop with smart notifications.",
      color: "from-[#8B4513] to-[#6B3A1A]",
      bgPattern: "bg-gradient-to-br from-orange-50 to-amber-50"
    },
    {
      id: "smart-scheduling",
      icon: faCalendarAlt,
      title: "Smart Scheduling",
      description: "Find common free time across multiple calendars and suggest optimal meeting windows that work for everyone.",
      color: "from-[#D2B48C] to-[#8B4513]",
      bgPattern: "bg-gradient-to-br from-amber-50 to-yellow-50"
    },
    {
      id: "natural-conversations",
      icon: faComments,
      title: "Natural Conversations",
      description: "Chat with Coffy like you would with a friend. No complex commands or confusing interfaces required.",
      color: "from-[#6B3A1A] to-[#4A2612]",
      bgPattern: "bg-gradient-to-br from-yellow-50 to-orange-50"
    },
    {
      id: "seamless-integration",
      icon: faLink,
      title: "Seamless Integration",
      description: "Connect with your favorite calendar apps, messaging platforms, and social media for a unified experience.",
      color: "from-[#8B4513] to-[#A0522D]",
      bgPattern: "bg-gradient-to-br from-yellow-50 to-orange-50"
    },
    {
      id: "ai-personalities",
      icon: faRobot,
      title: "AI-Powered Planning",
      description: "Let Coffy's AI handle the heavy lifting of coordination while you focus on having great conversations.",
      color: "from-[#4A2612] to-[#6B3A1A]",
      bgPattern: "bg-gradient-to-br from-amber-50 to-orange-50"
    },
  ]

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2
      }
    }
  }

  const itemVariants = {
    hidden: {
      opacity: 0,
      y: 30,
      scale: 0.95
    },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        duration: 0.6,
        ease: "easeOut"
      }
    }
  }

  return (
    <section
      ref={ref}
      id="features"
      className="py-24 lg:py-32 bg-gradient-to-br from-[#FFF8DC] via-[#F7F5F3] to-[#FAF0E6] relative overflow-hidden"
    >
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,rgba(139,69,19,0.02)_1px,transparent_0)] bg-[length:32px_32px]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_800px_600px_at_120%_200%,rgba(139,69,19,0.03)_0%,transparent_50%)]" />
      </div>

      <div className="container mx-auto px-6 relative">
        <motion.div
          className="text-center mb-20"
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.6 }}
        >
          <motion.div
            className="inline-flex items-center px-6 py-3 bg-white/70 backdrop-blur-sm rounded-full border border-[#8B4513]/10 mb-8 shadow-sm"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={inView ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <span className="text-[#8B4513] font-semibold text-sm tracking-wide uppercase">
              Features
            </span>
          </motion.div>

          <motion.h2
            className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 max-w-4xl mx-auto leading-tight"
            initial={{ opacity: 0, y: 20 }}
            animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            Everything You Need to{' '}
            <span className="bg-gradient-to-r from-[#8B4513] to-[#6B3A1A] bg-clip-text text-transparent">
              Connect & Plan
            </span>
          </motion.h2>

          <motion.p
            className="text-lg md:text-xl text-[#6B3A1A] max-w-3xl mx-auto leading-relaxed"
            initial={{ opacity: 0, y: 20 }}
            animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            Coffy brings the magic of effortless coordination to your social life.
            From spontaneous coffee runs to planned group activities, we've got you covered.
          </motion.p>
        </motion.div>
        <motion.div
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto"
          variants={containerVariants}
          initial="hidden"
          animate={inView ? "visible" : "hidden"}
        >
          {features.map((feature, index) => (
            <motion.div
              key={feature.id}
              variants={itemVariants}
              className="group"
            >
              <div className={`relative h-full p-8 ${feature.bgPattern} backdrop-blur-sm border border-white/50 rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 hover:-translate-y-2`}>

                <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent rounded-3xl" />

                <div className="relative">
                  <div className={`w-16 h-16 bg-gradient-to-br ${feature.color} rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 group-hover:rotate-3 transition-all duration-500 shadow-lg`}>
                    <FontAwesomeIcon
                      icon={feature.icon}
                      className="text-white text-xl filter drop-shadow-sm"
                    />
                  </div>

                  <h3 className="text-xl font-bold text-[#4A2612] mb-4 group-hover:text-[#8B4513] transition-colors duration-300">
                    {feature.title}
                  </h3>

                  <p className="text-[#6B3A1A] leading-relaxed text-sm">
                    {feature.description}
                  </p>

                  <div className="absolute bottom-4 right-4 w-2 h-2 bg-[#8B4513] rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
        <motion.div
          className="text-center mt-20"
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.6, delay: 0.8 }}
        >
          <div className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#8B4513] to-[#6B3A1A] text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <span className="text-sm font-medium">Ready to get started?</span>
            <FontAwesomeIcon icon={faUsers} className="text-sm" />
          </div>
        </motion.div>
      </div>
    </section>
  )
}

export default FeaturesSection
