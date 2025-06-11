'use client'

import { motion } from 'framer-motion'
import { useInView } from 'react-intersection-observer'
import { useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faRocket,
  faGift,
  faCoffee,
  faUsers,
  faEnvelope,
  faUser,
  faCheckCircle,
  faStar
} from '@fortawesome/free-solid-svg-icons'

const WaitlistSection = () => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  })

  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [isSubmitted, setIsSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (email && name) {
      setIsSubmitted(true)
      // Here you would typically send the data to your backend
      console.log('Waitlist signup:', { name, email })
    }
  }

const benefits = [
    {
        icon: faRocket,
        title: "Early Access",
        description: "Be among the first to experience Coffy and help shape the future of social planning with exclusive beta access.",
        color: "from-blue-500 to-blue-600"
    },
    {
        icon: faGift,
        title: "Free Features",
        description: "Join the waitlist for free and get exclusive early access to all premium features at launch.",
        color: "from-green-500 to-green-600"
    },
    {
        icon: faStar,
        title: "Exclusive Updates",
        description: "Get behind-the-scenes content and be the first to know about new features and improvements.",
        color: "from-orange-500 to-orange-600"
    }
]

  if (isSubmitted) {
    return (
      <section id="waitlist" className="py-24 bg-gradient-to-br from-[#8B4513] via-[#6B3A1A] to-[#4A2612]">
        <div className="container mx-auto px-6 text-center">
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.8, type: "spring", bounce: 0.4 }}
            className="max-w-2xl mx-auto"
          >
            <div className="bg-white/95 backdrop-blur-lg rounded-3xl p-12 shadow-2xl border border-white/20">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.6, delay: 0.3, type: "spring" }}
                className="w-20 h-20 bg-gradient-to-r from-green-500 to-green-600 rounded-full flex items-center justify-center mx-auto mb-6"
              >
                <FontAwesomeIcon icon={faCheckCircle} className="text-white text-3xl" />
              </motion.div>

              <motion.h2
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.5 }}
                className="text-4xl font-bold text-[#8B4513] mb-4"
              >
                Welcome to the Coffy Family!
              </motion.h2>

              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.7 }}
                className="text-xl text-[#6B3A1A] mb-6"
              >
                Thanks for joining our waitlist, {name}! We'll notify you as soon as Coffy is ready.
              </motion.p>

              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.9 }}
                className="text-[#6B3A1A]"
              >
                Keep an eye on your inbox for exclusive updates and early access opportunities.
              </motion.p>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 1.1 }}
                className="mt-8 flex justify-center gap-4"
              >
                <div className="flex items-center gap-2 text-[#6B3A1A]">
                  <FontAwesomeIcon icon={faCoffee} className="text-[#8B4513]" />
                  <span className="text-sm">Early Access</span>
                </div>
                <div className="flex items-center gap-2 text-[#6B3A1A]">
                  <FontAwesomeIcon icon={faUsers} className="text-[#8B4513]" />
                  <span className="text-sm">Community</span>
                </div>
                <div className="flex items-center gap-2 text-[#6B3A1A]">
                  <FontAwesomeIcon icon={faStar} className="text-[#8B4513]" />
                  <span className="text-sm">Exclusive Updates</span>
                </div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </section>
    )
  }

  return (
    <section id="waitlist" className="py-24 lg:py-32 bg-gradient-to-br from-[#8B4513] via-[#6B3A1A] to-[#4A2612] overflow-hidden relative">
      {/* Enhanced Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,rgba(255,255,255,0.02)_1px,transparent_0)] bg-[length:40px_40px]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_1200px_800px_at_80%_20%,rgba(255,255,255,0.03)_0%,transparent_50%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_800px_600px_at_20%_80%,rgba(255,248,220,0.02)_0%,transparent_50%)]" />
      </div>

      <div className="container mx-auto px-6 relative z-10">
        {/* Content inside the container */}
      </div>
        {/* Header Section */}
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
          className="text-center mb-20"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={inView ? { opacity: 1, scale: 1 } : {}}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="inline-flex items-center gap-2 px-6 py-3 bg-white/10 backdrop-blur-sm rounded-full border border-white/20 mb-8"
          >
            <FontAwesomeIcon icon={faUsers} className="text-white text-sm" />
            <span className="text-white font-medium text-sm uppercase tracking-wide">
              Join the Community
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-5xl lg:text-6xl font-bold text-white mb-6"
          >
            Join the{' '}
            <span className="bg-gradient-to-r from-[#FFF8DC] to-[#F7F5F3] bg-clip-text text-transparent">
              Coffy
            </span>{' '}
            Revolution
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="text-xl text-white/90 max-w-3xl mx-auto leading-relaxed"
          >
            Be part of the future of social planning. Get early access to Coffy and
            transform how you connect with friends and colleagues.
          </motion.p>
        </motion.div>

        <div className="max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left - Benefits */}
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={inView ? { opacity: 1, x: 0 } : {}}
              transition={{ duration: 0.8, delay: 0.4 }}
            >
              <h3 className="text-3xl font-bold text-white mb-8">
                Why Join the Waitlist?
              </h3>

              <div className="space-y-6">
                {benefits.map((benefit, index) => (
                  <motion.div
                    key={benefit.title}
                    initial={{ opacity: 0, x: -30 }}
                    animate={inView ? { opacity: 1, x: 0 } : {}}
                    transition={{ duration: 0.6, delay: 0.5 + index * 0.1 }}
                    className="flex items-start space-x-4"
                  >
                    <div className={`w-12 h-12 bg-gradient-to-r ${benefit.color} rounded-xl flex items-center justify-center flex-shrink-0`}>
                      <FontAwesomeIcon icon={benefit.icon} className="text-white text-lg" />
                    </div>
                    <div>
                      <h4 className="text-xl font-semibold text-white mb-2">
                        {benefit.title}
                      </h4>
                      <p className="text-white/80 leading-relaxed">
                        {benefit.description}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Right - Signup Form */}
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={inView ? { opacity: 1, x: 0 } : {}}
              transition={{ duration: 0.8, delay: 0.6 }}
            >

            <div className="bg-white/15 backdrop-blur-lg rounded-3xl p-10 border border-white/30 shadow-2xl">
              <div className="text-center mb-8">
                <motion.div
                  animate={{
                  y: [-3, 3, -3],
                  rotate: [-1, 1, -1]
                  }}
                  transition={{
                  duration: 4,
                  repeat: Number.POSITIVE_INFINITY,
                  ease: "easeInOut"
                  }}
                  className="w-20 h-20 bg-gradient-to-r from-[#FFF8DC] to-[#F7F5F3] rounded-full flex items-center justify-center mx-auto mb-6"
                >
                  <img src="logo.png" alt="Logo" className="w-12 h-12" />
                </motion.div>
                <h3 className="text-3xl font-bold text-white mb-2">
                  Get Early Access
                </h3>
                <p className="text-white/80">
                  Join the coffy lovers already on the waitlist
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="relative">
                  <FontAwesomeIcon icon={faUser} className="absolute left-4 top-1/2 transform -translate-y-1/2 text-white/60" />
                  <input
                    type="text"
                    placeholder="Your Name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full pl-12 pr-6 py-4 rounded-2xl bg-white/20 border border-white/30 text-white placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-[#FFF8DC] focus:border-transparent backdrop-blur-sm transition-all duration-300"
                    required
                  />
                </div>

                <div className="relative">
                  <FontAwesomeIcon icon={faEnvelope} className="absolute left-4 top-1/2 transform -translate-y-1/2 text-white/60" />
                  <input
                    type="email"
                    placeholder="Your Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-12 pr-6 py-4 rounded-2xl bg-white/20 border border-white/30 text-white placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-[#FFF8DC] focus:border-transparent backdrop-blur-sm transition-all duration-300"
                    required
                  />
                </div>

                <motion.button
                  type="submit"
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full bg-gradient-to-r from-[#FFF8DC] to-[#F7F5F3] text-[#8B4513] px-8 py-4 rounded-2xl font-bold text-lg shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center gap-2"
                >
                  <FontAwesomeIcon icon={faRocket} />
                  Join the Waitlist
                </motion.button>
              </form>

              <div className="mt-8 text-center">
                <p className="text-sm text-white/70 mb-4">
                  🔒 We respect your privacy. No spam, ever. Unsubscribe anytime.
                </p>

                <div className="flex justify-center gap-6 text-sm text-white/60">
                  <div className="flex items-center gap-1">
                    <FontAwesomeIcon icon={faCheckCircle} />
                    <span>No spam</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}

export default WaitlistSection
