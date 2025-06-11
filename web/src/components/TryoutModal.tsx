'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogTrigger } from '@/components/ui/dialog'
import { User, Moon, Wifi, Battery, ArrowLeft } from 'lucide-react'

interface TryoutModalProps {
  children: React.ReactNode
}

interface Message {
  id: string
  text: string
  isUser: boolean
  timestamp: Date
}

interface ChatFlow {
  responses: string[]
  nextQuestions?: string[]
}

export default function TryoutModal({ children }: TryoutModalProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [showChat, setShowChat] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const [currentQuestions, setCurrentQuestions] = useState<string[]>([])


  const initialQuestions = [
    "What can you help me with today?",
    "Tell me about your features",
    "Set up a meeting sometime this week",
    "Plan dinner for my friend group"
  ]

  // Significantly expanded conversation system
  const chatFlows: Record<string, ChatFlow> = {
    "What can you help me with today?": {
      responses: [
        "I can help you coordinate coffee dates, plan group hangouts, schedule meetings with friends, and organize social events! Just tell me what you'd like to do and I'll help make it happen. ☕",
        "I'm basically your social planning assistant! Whether it's a quick coffee catch-up or a big group celebration, I've got you covered."
      ],
      nextQuestions: [
        "I want to plan a coffee date",
        "Help me organize a group event",
        "I need to schedule a business meeting",
        "Show me what else you can do"
      ]
    },

    "Tell me about your features": {
      responses: [
        "I'm your AI companion for social planning! I can:",
        "• Coordinate coffee dates\n• Schedule group meetups\n• Find the best times for everyone\n• Suggest great locations\n• Send invitations\n• Handle RSVPs",
        "What would you like to try first?"
      ],
      nextQuestions: [
        "Help me find a coffee spot",
        "Coordinate schedules for a group",
        "Send invitations to friends",
        "Find the perfect meeting location"
      ]
    },

    "Set up a meeting sometime this week": {
      responses: [
        "Great! Let me help you set up a meeting this week. Who would you like to meet with?",
        "I can suggest some great spots and find times that work for everyone! 📅"
      ],
      nextQuestions: [
        "It's a business meeting with 2-3 people",
        "Casual coffee with a close friend",
        "Team meeting with 5+ colleagues",
        "One-on-one mentoring session"
      ]
    },

    "Plan dinner for my friend group": {
      responses: [
        "Perfect! Planning a group dinner is one of my specialties! 🍽️",
        "How many friends are we talking about? I can help you find a restaurant that fits everyone's taste, coordinate schedules, make reservations, and send out invites."
      ],
      nextQuestions: [
        "Small group (3-4 friends)",
        "Medium group (5-8 friends)",
        "Large group (9+ friends)",
        "Help me pick a restaurant type"
      ]
    },

    // Coffee Date Planning Branch
    "I want to plan a coffee date": {
      responses: [
        "Coffee dates are my favorite! ☕ Let me help you make this perfect.",
        "Are you thinking somewhere cozy for deep conversation, or a bustling café with great energy?"
      ],
      nextQuestions: [
        "Cozy and intimate spot",
        "Trendy café with good wifi",
        "Outdoor seating preferred",
        "Help me pick the best time"
      ]
    },

    "Cozy and intimate spot": {
      responses: [
        "I love that choice! Cozy spots are perfect for meaningful conversations. ☕",
        "I'm thinking small independent cafés with comfortable seating, maybe some books on the shelves, and that perfect lighting for great photos too!"
      ],
      nextQuestions: [
        "Find spots with outdoor seating",
        "Places with the best pastries",
        "Cafés with a bookish vibe",
        "Schedule the perfect time"
      ]
    },

    "Trendy café with good wifi": {
      responses: [
        "Smart choice! Perfect for those coffee dates that might turn into work sessions. 💻",
        "I know some amazing spots with reliable wifi, great coffee, and that trendy atmosphere where you'll want to post photos!"
      ],
      nextQuestions: [
        "Find cafés with laptop-friendly policies",
        "Places with the best Instagram potential",
        "Spots near public transportation",
        "Help coordinate our schedules"
      ]
    },

    "Outdoor seating preferred": {
      responses: [
        "Outdoor coffee dates are magical! ☀️ Fresh air and great conversation - perfect combo.",
        "I can help you find spots with beautiful patios, garden seating, or even rooftop terraces depending on your vibe!"
      ],
      nextQuestions: [
        "Find places with garden patios",
        "Rooftop café terraces",
        "Sidewalk people-watching spots",
        "Check the weather forecast"
      ]
    },

    // Group Event Planning Branch
    "Help me organize a group event": {
      responses: [
        "Group events are so much fun! 🎉 I love bringing people together.",
        "What kind of vibe are you going for? Casual hangout, celebration, or something more structured?"
      ],
      nextQuestions: [
        "Birthday celebration",
        "Casual weekend hangout",
        "Holiday party planning",
        "Work team building event"
      ]
    },

    "Birthday celebration": {
      responses: [
        "Birthday parties are the best! 🎂 Let's make this one unforgettable.",
        "Are we thinking intimate dinner party, big bash, or maybe something totally unique like an activity-based celebration?"
      ],
      nextQuestions: [
        "Intimate dinner party (8-12 people)",
        "Big birthday bash (20+ people)",
        "Activity-based celebration",
        "Surprise party planning"
      ]
    },

    "Casual weekend hangout": {
      responses: [
        "Weekend hangouts are perfect for reconnecting with friends! 😊",
        "I can help you plan something super chill - maybe brunch, park picnic, game night, or bar hopping?"
      ],
      nextQuestions: [
        "Weekend brunch spots",
        "Perfect picnic locations",
        "Board game café night",
        "Bar crawl route planning"
      ]
    },

    // Business Meeting Branch
    "It's a business meeting with 2-3 people": {
      responses: [
        "Perfect! For a small business meeting, I'd recommend a quiet café or a professional co-working space.",
        "I can help you find spots with good wifi, minimal noise, and comfortable seating for productive discussions. 💼"
      ],
      nextQuestions: [
        "Find a quiet café nearby",
        "Book a meeting room",
        "Suggest the best times",
        "Help coordinate everyone's schedule"
      ]
    },

    "Team meeting with 5+ colleagues": {
      responses: [
        "Larger team meetings need special consideration! 👥",
        "I can help you find conference rooms, private dining areas, or even unique venues that'll make your meeting memorable and productive."
      ],
      nextQuestions: [
        "Reserve a conference room",
        "Private dining meeting",
        "Unique venue options",
        "Virtual + in-person hybrid setup"
      ]
    },

    // Restaurant Planning Branch
    "Small group (3-4 friends)": {
      responses: [
        "A small group is perfect for trying that new restaurant everyone's been talking about! 🍽️",
        "I can help you find intimate spots where you can actually hear each other talk. Much better than those super loud places!"
      ],
      nextQuestions: [
        "Find a new trendy restaurant",
        "Casual dining spot",
        "Help pick a cuisine type",
        "Check everyone's availability"
      ]
    },

    "Medium group (5-8 friends)": {
      responses: [
        "Medium groups are tricky but so fun! 🍻 You need somewhere with good group seating.",
        "I can help you find restaurants with big tables, private dining rooms, or places that take reservations for larger parties."
      ],
      nextQuestions: [
        "Restaurants with private rooms",
        "Places with large communal tables",
        "Family-style dining options",
        "Split the bill friendly spots"
      ]
    },

    "Large group (9+ friends)": {
      responses: [
        "Wow, a big celebration! 🎉 Large groups definitely need special planning.",
        "I'd recommend restaurants with private event spaces, family-style serving, or maybe even food trucks for a fun twist!"
      ],
      nextQuestions: [
        "Private event spaces",
        "Buffet or family-style restaurants",
        "Food truck catering",
        "Venue with entertainment options"
      ]
    },

    // Deep Cuisine Exploration
    "Help pick a cuisine type": {
      responses: [
        "Ooh, choosing cuisine is one of my favorite parts! 🌍",
        "Let me help you explore options based on your group's preferences, dietary restrictions, and adventure level!"
      ],
      nextQuestions: [
        "Italian comfort food vibes",
        "Asian fusion adventure",
        "Mexican fiesta planning",
        "Farm-to-table local spots"
      ]
    },

    "Italian comfort food vibes": {
      responses: [
        "Pasta brings people together like nothing else! 🍝",
        "I can find you authentic trattorias, modern Italian bistros, or even places with amazing wine pairings for the full experience."
      ],
      nextQuestions: [
        "Authentic family-owned places",
        "Modern Italian with cocktails",
        "Pizza party locations",
        "Wine bar with small plates"
      ]
    },

    // Schedule Coordination Branch
    "Check everyone's availability": {
      responses: [
        "Schedule coordination is my superpower! 📅 Let me help you find the perfect time.",
        "I can help you poll everyone's availability, suggest optimal times, and even handle the back-and-forth coordination."
      ],
      nextQuestions: [
        "Send availability poll to group",
        "Find best times for weekday dinner",
        "Weekend brunch coordination",
        "Handle dietary restrictions too"
      ]
    },

    "Help coordinate everyone's schedule": {
      responses: [
        "Coordinating schedules can be tricky, but I've got strategies! ⏰",
        "I can help you find time slots that work for everyone, suggest backup dates, and even remind people to respond."
      ],
      nextQuestions: [
        "Find overlapping free time",
        "Suggest multiple date options",
        "Set up reminder system",
        "Plan backup dates"
      ]
    },

    // Location-specific branches
    "Find spots with outdoor seating": {
      responses: [
        "Outdoor dining makes everything better! 🌞",
        "I know places with beautiful patios, rooftop views, and garden settings that'll make your coffee date absolutely perfect."
      ],
      nextQuestions: [
        "Rooftop terraces with city views",
        "Garden courtyards",
        "Waterfront seating",
        "Street-side people watching"
      ]
    },

    "Places with the best pastries": {
      responses: [
        "A coffee date isn't complete without amazing pastries! 🥐",
        "I can find you spots with fresh croissants, artisanal donuts, or even places that make their own macarons!"
      ],
      nextQuestions: [
        "French bakery vibes",
        "Artisanal donut shops",
        "Local pastry makers",
        "Healthy breakfast options"
      ]
    },

    // Advanced planning features
    "Show me what else you can do": {
      responses: [
        "Oh, I have so many tricks up my sleeve! 🎩",
        "I can help with surprise parties, find the perfect brunch spot, coordinate carpools, suggest activities based on weather, and even help with gift planning for group events!"
      ],
      nextQuestions: [
        "Plan a surprise party",
        "Find the perfect brunch spot",
        "Help with transportation",
        "Weather-based activity ideas"
      ]
    },

    "Plan a surprise party": {
      responses: [
        "Surprise parties are SO exciting! 🎉 The secret planning is half the fun.",
        "I can help you coordinate the guest list, find a venue, plan the perfect timing, and keep everything under wraps!"
      ],
      nextQuestions: [
        "Guest list coordination",
        "Venue that can keep secrets",
        "Perfect surprise timing",
        "Backup plans if they find out"
      ]
    },

    "Help with transportation": {
      responses: [
        "Getting everyone to the same place can be a challenge! 🚗",
        "I can help coordinate carpools, suggest central meeting spots, or even help with public transit planning."
      ],
      nextQuestions: [
        "Organize carpools",
        "Find central meeting locations",
        "Public transit coordination",
        "Parking situation planning"
      ]
    },

    // Weather and seasonal planning
    "Weather-based activity ideas": {
      responses: [
        "Weather can make or break plans! ☀️🌧️ But I always have backup ideas.",
        "I can suggest indoor alternatives for rainy days, outdoor options for beautiful weather, and everything in between!"
      ],
      nextQuestions: [
        "Rainy day backup plans",
        "Perfect sunny day activities",
        "Cozy indoor winter ideas",
        "Spring outdoor adventures"
      ]
    },

    // Additional engaging responses
    "Rainy day backup plans": {
      responses: [
        "Rainy days call for cozy indoor adventures! 🌧️☕",
        "I love planning backup activities - indoor escape rooms, cooking classes, board game cafés, art galleries, or even a wine tasting at home with friends!"
      ],
      nextQuestions: [
        "Find indoor escape rooms",
        "Cooking class experiences",
        "Board game café options",
        "Plan a cozy home gathering"
      ]
    },

    "Perfect sunny day activities": {
      responses: [
        "Sunny days are made for outdoor fun! ☀️🌳",
        "Think rooftop brunches, park picnics, outdoor markets, hiking trails with coffee stops, or even outdoor yoga classes followed by smoothies!"
      ],
      nextQuestions: [
        "Find rooftop brunch spots",
        "Plan the perfect picnic",
        "Outdoor market adventures",
        "Active outdoor meetups"
      ]
    },

    "Find a new trendy restaurant": {
      responses: [
        "Ooh, I love discovering new spots! 🍽️✨",
        "I can help you find the latest hotspots everyone's talking about - from Instagram-worthy interiors to innovative menus that'll give you all the conversation starters!"
      ],
      nextQuestions: [
        "Instagram-worthy restaurant spots",
        "Innovative cuisine experiences",
        "Chef's table dining",
        "Secret menu discoveries"
      ]
    }
  }

  const handleQuestionClick = async (question: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text: question,
      isUser: true,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setIsTyping(true)
    setCurrentQuestions([])
    await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 1000))

    setIsTyping(false)

    const flow = chatFlows[question]
    if (flow) {
      for (let i = 0; i < flow.responses.length; i++) {
        await new Promise(resolve => setTimeout(resolve, i === 0 ? 300 : 1200))

        const joeMessage: Message = {
          id: `${Date.now()}-${i}`,
          text: flow.responses[i],
          isUser: false,
          timestamp: new Date()
        }

        setMessages(prev => [...prev, joeMessage])
      }

      await new Promise(resolve => setTimeout(resolve, 800))
      setCurrentQuestions(flow.nextQuestions || [])
    }
  }

  const handleBackToWelcome = () => {
    setShowChat(false)
    setMessages([])
    setCurrentQuestions([])
    setIsTyping(false)
  }

  const startChat = (question: string) => {
    setShowChat(true)
    handleQuestionClick(question)
  }
  const scrollToBottom = () => {
    if (typeof window !== 'undefined') {
      setTimeout(() => {
        const chatContainer = document.getElementById('chat-messages')
        if (chatContainer) {
          chatContainer.scrollTop = chatContainer.scrollHeight
        }
      }, 100)
    }
  }

  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom()
    }
  }, [messages])
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            if (showChat && currentQuestions.length > 0) {
            handleQuestionClick(currentQuestions[0])
            }
        }
        }
    
        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [showChat, currentQuestions, handleQuestionClick])

  useEffect(() => {
    if (isTyping) {
      scrollToBottom()
    }
  }, [isTyping])

  scrollToBottom()

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {children}
      </DialogTrigger>
      <DialogContent className="max-w-md sm:max-w-lg lg:max-w-xl p-0 border-0 bg-transparent shadow-none max-h-[90vh]">
        <div className="relative mx-auto">
          <div className="w-80 sm:w-96 lg:w-[420px] h-[600px] sm:h-[700px] lg:h-[800px] bg-black rounded-[2.5rem] p-2 shadow-2xl">
            <div className="w-full h-full bg-[#F7F5F3] rounded-[2rem] overflow-hidden flex flex-col">
              <div className="flex justify-between items-center px-6 pt-4 pb-2 text-black text-sm font-medium">
                <div className="flex items-center gap-1">
                  <span>{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="flex items-center gap-1">
                    <Battery size={16} />
                    <span className="text-xs">37%</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-between items-center px-6 py-3 border-b border-[#E5E1DB]">
                <div className="flex items-center gap-3">
                  {showChat && (
                    <button
                      onClick={handleBackToWelcome}
                      className="mr-2 p-1 hover:bg-[#E5E1DB] rounded-full transition-colors"
                    >
                      <ArrowLeft size={20} className="text-[#8B4513]" />
                    </button>
                  )}
                  <div className="w-8 h-8 rounded-full overflow-hidden">
                    <img
                      src="logo.png"
                      alt="Coffy"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <span className="text-[#8B4513] font-semibold">Joe</span>
                </div>
                <div className="w-8 h-8 bg-[#FFF8DC] rounded-full flex items-center justify-center">
                  <User size={16} className="text-[#8B4513]" />
                </div>
              </div>

              {/* Main Content */}
              <div className="flex-1 flex flex-col overflow-hidden">
                {!showChat ? (
                  // Welcome Screen
                  <div className="flex-1 flex flex-col justify-center px-6 py-8">
                    {/* Large Coffee Cup Illustration */}
                    <div className="flex justify-center mb-6">
                      <div className="relative">
                        <div className="w-32 h-32 bg-[#FFF8DC] rounded-full flex items-center justify-center">
                          <img
                            src="image.png"
                            alt="Joe waving"
                            className="w-24 h-24 object-contain"
                          />
                        </div>
                        {/* Speech bubble */}
                        <div className="absolute -top-2 -right-4 bg-white rounded-2xl px-3 py-1 shadow-md border border-[#E5E1DB]">
                          <span className="text-[#8B4513] text-sm font-medium">Hi!</span>
                          <div className="absolute bottom-0 left-4 w-0 h-0 border-l-4 border-l-transparent border-r-4 border-r-transparent border-t-4 border-t-white" />
                        </div>
                      </div>
                    </div>

                    {/* Headline */}
                    <h1 className="text-2xl font-bold text-[#8B4513] text-center mb-3">
                      Hi, I'm Joe!
                    </h1>

                    {/* Description */}
                    <p className="text-[#6B3A1A] text-center mb-8 leading-relaxed text-sm sm:text-base">
                      I'm Joe, ready to help you grab Coffy with all your friends and companions
                    </p>

                    {/* Preset Question Buttons */}
                    <div className="space-y-3 mb-8">
                      {initialQuestions.map((question) => (
                        <button
                          key={question}
                          onClick={() => startChat(question)}
                          className="w-full bg-[#FFF8DC] hover:bg-[#F5DEB3] text-[#8B4513] font-medium py-3 sm:py-4 px-4 sm:px-6 rounded-full text-left transition-colors text-sm sm:text-base"
                        >
                          {question}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  // Chat Screen - Fixed 2/3 and 1/3 split
                  <div className="flex-1 flex flex-col">
                    {/* Top 2/3 - Scrollable Chat History */}
                    <div
                      id="chat-messages"
                      className="h-2/3 overflow-y-auto overflow-x-hidden px-6 py-4 space-y-4 scroll-smooth"
                      style={{
                        scrollbarWidth: 'thin',
                        scrollbarColor: '#D2B48C #F7F5F3'
                      }}
                    >
                      {messages.map((message) => (
                        <div
                          key={message.id}
                          className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                        >
                          <div className="flex items-start gap-2 max-w-[85%]">
                            {!message.isUser && (
                              <div className="w-6 h-6 rounded-full overflow-hidden flex-shrink-0 mt-1">
                                <img
                                  src="image.png"
                                  alt="Joe"
                                  className="w-full h-full object-cover"
                                />
                              </div>
                            )}
                            <div
                              className={`rounded-2xl px-4 py-3 text-sm whitespace-pre-line ${
                                message.isUser
                                  ? 'bg-[#8B4513] text-white rounded-br-md'
                                  : 'bg-[#FFF8DC] text-[#8B4513] rounded-bl-md'
                              }`}
                            >
                              {message.text}
                            </div>
                          </div>
                        </div>
                      ))}
                      {isTyping && (
                        <div className="flex justify-start">
                          <div className="flex items-start gap-2 max-w-[85%]">
                            <div className="w-6 h-6 rounded-full overflow-hidden flex-shrink-0 mt-1">
                              <img
                                src="image.png"
                                alt="Joe"
                                className="w-full h-full object-cover"
                              />
                            </div>
                            <div className="bg-[#FFF8DC] rounded-2xl rounded-bl-md px-4 py-3">
                              <div className="flex space-x-1">
                                <div className="w-2 h-2 bg-[#8B4513] rounded-full animate-bounce" style={{animationDelay: '0ms'}} />
                                <div className="w-2 h-2 bg-[#8B4513] rounded-full animate-bounce" style={{animationDelay: '150ms'}} />
                                <div className="w-2 h-2 bg-[#8B4513] rounded-full animate-bounce" style={{animationDelay: '300ms'}} />
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Bottom 1/3 - Fixed Interactive Options */}
                    <div className="h-1/3 border-t border-[#E5E1DB]/50 bg-[#F7F5F3] flex flex-col">
                      <div className="px-6 pt-3 pb-4 flex-1 flex flex-col justify-center overflow-hidden">
                        <div className="space-y-2">
                          {currentQuestions.slice(0, 3).map((question) => (
                            <button
                              key={question}
                              onClick={() => handleQuestionClick(question)}
                              className="w-full bg-[#E5E1DB] hover:bg-[#D2B48C] text-[#8B4513] font-medium py-2.5 px-4 rounded-full text-left transition-colors text-sm border border-[#8B4513]/20 shadow-sm"
                            >
                              {question}
                            </button>
                          ))}
                          {currentQuestions.length > 3 && (
                            <div className="text-center text-xs text-[#8B4513]/60 pt-1">
                              +{currentQuestions.length - 3} more options available
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Bottom space for design consistency */}
              <div className="h-2" />

            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
