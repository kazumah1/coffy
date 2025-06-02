import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  ScrollView, 
  StyleSheet, 
  StatusBar,
  KeyboardAvoidingView,
  Platform,
  Dimensions,
  Animated,
  Easing
} from 'react-native';
import { Image } from 'expo-image';
import { router, useLocalSearchParams } from 'expo-router';
import { useAuth } from '@/contexts/AuthContext';

const { width, height } = Dimensions.get('window');

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

// Coffee-themed color palette following the source design
const colors = {
  coffeeDark: '#4A3728',
  coffeeMedium: '#8B4513',
  coffeeLight: '#D2B48C',
  coffeeCream: '#F5F5DC',
  coffeeWhite: '#FFFEF7',
  coffeeAccent: '#CD853F',
  textPrimary: '#2D1B12',
  textSecondary: '#6B4E3D',
  textLight: '#8B7355',
  background: '#FFFEF7',
};

const WELCOME_SUGGESTIONS = [
  "What can you help me with today?",
  "Tell me about your features",
  "Set up a meeting sometime this week",
  "Plan dinner for my friend group"
];

const BACKEND_URL = "http://localhost:8000";
const WS_URL = "ws://localhost:8000";

export default function ChatScreen() {
  const { user } = useAuth();
  const params = useLocalSearchParams();
  const autoPrompt = params.autoPrompt as string;
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);
  const wsRef = useRef<WebSocket | null>(null);
  
  // Animation values
  const messageAnimations = useRef<{[key: string]: Animated.Value}>({});
  const inputFocusAnim = useRef(new Animated.Value(0)).current;
  const welcomeAnim = useRef(new Animated.Value(0)).current;

  // WebSocket connection
  useEffect(() => {
    if (!user?.id) {
      console.log('No user ID available, skipping WebSocket connection');
      return;
    }

    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const reconnectDelay = 3000;

    const connectWebSocket = () => {
      if (reconnectAttempts >= maxReconnectAttempts) {
        console.log('Max reconnection attempts reached');
        return;
      }

      console.log('Attempting WebSocket connection...');
      console.log('Connecting to WebSocket:', `${WS_URL}/llm/ws/${user.id}`);
      wsRef.current = new WebSocket(`${WS_URL}/llm/ws/${user.id}`);
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected successfully');
        reconnectAttempts = 0; // Reset reconnect attempts on successful connection
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'chat_message') {
            const botMessage: Message = {
              id: (Date.now() + 1).toString(),
              text: data.message,
              isUser: false,
              timestamp: new Date()
            };
            setMessages(prev => [...prev, botMessage]);
            animateNewMessage(botMessage.id);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        const errorMessage: Message = {
          id: Date.now().toString(),
          text: 'Connection error. Attempting to reconnect...',
          isUser: false,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        
        // Don't reconnect if it was a normal closure
        if (event.code === 1000) {
          return;
        }

        // Attempt to reconnect
        reconnectAttempts++;
        if (reconnectAttempts < maxReconnectAttempts) {
          console.log(`Reconnecting... Attempt ${reconnectAttempts} of ${maxReconnectAttempts}`);
          setTimeout(connectWebSocket, reconnectDelay);
        } else {
          const errorMessage: Message = {
            id: Date.now().toString(),
            text: 'Unable to establish connection. Please refresh the page.',
            isUser: false,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, errorMessage]);
        }
      };
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounting');
      }
    };
  }, [user?.id]);

  // Welcome screen animation
  useEffect(() => {
    if (messages.length === 0 && !autoPrompt) {
      Animated.timing(welcomeAnim, {
        toValue: 1,
        duration: 800,
        easing: Easing.out(Easing.ease),
        useNativeDriver: true,
      }).start();
    }
  }, [messages, autoPrompt]);

  // Handle auto-prompt from quick actions
  useEffect(() => {
    if (autoPrompt && messages.length === 0) {
      // Automatically send the prompt
      setTimeout(() => {
        sendMessage(autoPrompt);
      }, 500);
    }
  }, [autoPrompt]);

  const animateNewMessage = (messageId: string) => {
    const anim = new Animated.Value(0);
    messageAnimations.current[messageId] = anim;
    
    Animated.sequence([
      Animated.timing(anim, {
        toValue: 1,
        duration: 500,
        easing: Easing.out(Easing.back(1.1)),
        useNativeDriver: true,
      })
    ]).start();
  };

  const sendMessage = async (messageText?: string) => {
    const textToSend = messageText || inputText.trim();
    if (!textToSend || !user) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: textToSend,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    animateNewMessage(userMessage.id);
    setInputText('');
    setIsLoading(true);

    // Animate input focus out
    Animated.timing(inputFocusAnim, {
      toValue: 0,
      duration: 200,
      useNativeDriver: false,
    }).start();

    try {
      const response = await fetch(`${BACKEND_URL}/llm/prompt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          request: textToSend,
          creator_id: user.id
        }),
      });

      const data = await response.json();
      
      let responseText = 'Sorry, I encountered an error. Please try again.';
      if (data && data.response) {
        if (data.response.content) {
          responseText = data.response.content;
        } else if (typeof data.response === 'string') {
          responseText = data.response;
        }
      }
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: responseText,
        isUser: false,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
      animateNewMessage(botMessage.id);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I encountered an error. Please try again.',
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      animateNewMessage(errorMessage.id);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    scrollViewRef.current?.scrollToEnd({ animated: true });
  }, [messages]);

  const goBack = () => {
    router.back();
  };

  const onInputFocus = () => {
    Animated.timing(inputFocusAnim, {
      toValue: 1,
      duration: 200,
      useNativeDriver: false,
    }).start();
  };

  const onInputBlur = () => {
    Animated.timing(inputFocusAnim, {
      toValue: 0,
      duration: 200,
      useNativeDriver: false,
    }).start();
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const inputBorderColor = inputFocusAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [`${colors.coffeeMedium}20`, `${colors.coffeeMedium}60`],
  });

  const inputShadowOpacity = inputFocusAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.1, 0.25],
  });

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.background} />
      
      {/* Minimal Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={goBack}>
          <Text style={styles.backButtonText}>✕</Text>
        </TouchableOpacity>
        <View style={styles.logoContainer}>
          <View style={styles.coffeeLogo}>
            <Image 
              source={require('@/assets/images/coffee-character.png')} 
              style={styles.logoImage}
              contentFit="cover"
            />
          </View>
          <Text style={styles.appName}>Joe</Text>
        </View>
      </View>

      {/* Main Chat Area */}
      <View style={styles.chatContainer}>
        {messages.length === 0 && !autoPrompt ? (
          // Welcome Screen (only show if no auto-prompt)
          <Animated.View 
            style={[
              styles.welcomeScreen,
              {
                opacity: welcomeAnim,
                transform: [
                  {
                    translateY: welcomeAnim.interpolate({
                      inputRange: [0, 1],
                      outputRange: [50, 0],
                    }),
                  },
                ],
              },
            ]}
          >
            <Image 
              source={require('@/assets/images/coffee-character.png')} 
              style={styles.welcomeCharacter}
              contentFit="contain"
            />
            <View style={styles.welcomeTextContainer}>
              <Text style={styles.welcomeTitle}>Hi, I'm Joe!</Text>
              <Text style={styles.welcomeSubtitle}>
                I'm Joe, ready to help you grab Coffy with all your friends and companions
              </Text>
            </View>
            <View style={styles.suggestedMessages}>
              {WELCOME_SUGGESTIONS.map((suggestion, index) => (
                <TouchableOpacity
                  key={suggestion}
                  style={[
                    styles.suggestionButton,
                    { 
                      opacity: welcomeAnim,
                      transform: [
                        {
                          translateY: welcomeAnim.interpolate({
                            inputRange: [0, 1],
                            outputRange: [30, 0],
                          }),
                        },
                      ],
                    },
                  ]}
                  onPress={() => sendMessage(suggestion)}
                >
                  <Text style={styles.suggestionText}>{suggestion}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </Animated.View>
        ) : (
          // Messages
          <ScrollView 
            ref={scrollViewRef}
            style={styles.messagesContainer}
            contentContainerStyle={styles.messagesContent}
            showsVerticalScrollIndicator={false}
          >
            {messages.map((message) => {
              const messageAnim = messageAnimations.current[message.id] || new Animated.Value(1);
              
              return (
                <Animated.View
                  key={message.id}
                  style={[
                    styles.messageGroup,
                    message.isUser ? styles.userMessageGroup : styles.botMessageGroup,
                    {
                      opacity: messageAnim,
                      transform: [
                        {
                          translateY: messageAnim.interpolate({
                            inputRange: [0, 1],
                            outputRange: [30, 0],
                          }),
                        },
                        {
                          scale: messageAnim.interpolate({
                            inputRange: [0, 0.8, 1],
                            outputRange: [0.3, 1.05, 1],
                          }),
                        },
                      ],
                    },
                  ]}
                >
                  <View style={[
                    styles.messageBubble,
                    message.isUser ? styles.userBubble : styles.botBubble
                  ]}>
                    <Text style={[
                      styles.messageText,
                      message.isUser ? styles.userText : styles.botText
                    ]}>
                      {message.text}
                    </Text>
                  </View>
                  <Text style={[
                    styles.messageTime,
                    message.isUser ? styles.userTimeText : styles.botTimeText
                  ]}>
                    {formatTime(message.timestamp)}
                  </Text>
                </Animated.View>
              );
            })}
            
            {isLoading && (
              <View style={styles.typingIndicator}>
                <View style={styles.typingBubble}>
                  <View style={styles.typingDots}>
                    <Animated.View style={[styles.dot, styles.dot1]} />
                    <Animated.View style={[styles.dot, styles.dot2]} />
                    <Animated.View style={[styles.dot, styles.dot3]} />
                  </View>
                  <Text style={styles.typingText}>Joe is thinking...</Text>
                </View>
              </View>
            )}
          </ScrollView>
        )}

        {/* Enhanced Input Area */}
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.inputContainer}
        >
          <Animated.View 
            style={[
              styles.inputWrapper,
              {
                borderColor: inputBorderColor,
                shadowOpacity: inputShadowOpacity,
              }
            ]}
          >
            <TextInput
              style={styles.textInput}
              value={inputText}
              onChangeText={setInputText}
              onFocus={onInputFocus}
              onBlur={onInputBlur}
              placeholder="Ask me anything..."
              placeholderTextColor={colors.textLight}
              multiline
              maxLength={500}
              textAlignVertical="center"
            />
            <TouchableOpacity 
              style={[
                styles.sendButton, 
                !inputText.trim() && styles.sendButtonDisabled
              ]} 
              onPress={() => sendMessage()}
              disabled={!inputText.trim() || isLoading}
            >
              <Text style={styles.sendButtonText}>↗</Text>
            </TouchableOpacity>
          </Animated.View>
        </KeyboardAvoidingView>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 60,
    paddingBottom: 20,
    paddingHorizontal: 20,
    backgroundColor: colors.background,
    borderBottomWidth: 1,
    borderBottomColor: `${colors.coffeeMedium}10`,
    position: 'relative',
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  coffeeLogo: {
    width: 40,
    height: 40,
    backgroundColor: colors.coffeeMedium,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 3,
    overflow: 'hidden',
  },
  logoImage: {
    width: 40,
    height: 40,
    borderRadius: 20,
  },
  appName: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.coffeeDark,
    letterSpacing: -0.5,
  },
  backButton: {
    position: 'absolute',
    left: 20,
    top: 60,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.coffeeCream,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  backButtonText: {
    fontSize: 16,
    color: colors.coffeeDark,
    fontWeight: '500',
  },
  chatContainer: {
    flex: 1,
    backgroundColor: colors.background,
  },
  welcomeScreen: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 30,
    paddingBottom: 180,
    gap: 24,
  },
  welcomeCharacter: {
    width: 120,
    height: 120,
    borderRadius: 60,
    marginBottom: 10,
  },
  welcomeTextContainer: {
    alignItems: 'center',
    gap: 8,
  },
  welcomeTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: colors.coffeeDark,
    textAlign: 'center',
  },
  welcomeSubtitle: {
    fontSize: 16,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    maxWidth: 280,
  },
  suggestedMessages: {
    width: '100%',
    maxWidth: 320,
    gap: 12,
  },
  suggestionButton: {
    backgroundColor: colors.coffeeCream,
    borderWidth: 1,
    borderColor: `${colors.coffeeMedium}15`,
    paddingVertical: 16,
    paddingHorizontal: 20,
    borderRadius: 20,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  suggestionText: {
    fontSize: 15,
    color: colors.textPrimary,
    textAlign: 'center',
    fontWeight: '500',
  },
  messagesContainer: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  messagesContent: {
    paddingBottom: 100,
    gap: 16,
  },
  messageGroup: {
    maxWidth: '85%',
    gap: 4,
  },
  userMessageGroup: {
    alignSelf: 'flex-end',
    alignItems: 'flex-end',
  },
  botMessageGroup: {
    alignSelf: 'flex-start',
    alignItems: 'flex-start',
  },
  messageBubble: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 20,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  userBubble: {
    backgroundColor: colors.coffeeDark,
    borderBottomRightRadius: 6,
  },
  botBubble: {
    backgroundColor: colors.coffeeCream,
    borderBottomLeftRadius: 6,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
    fontWeight: '400',
  },
  userText: {
    color: colors.coffeeWhite,
  },
  botText: {
    color: colors.textPrimary,
  },
  messageTime: {
    fontSize: 12,
    marginTop: 4,
  },
  userTimeText: {
    color: colors.textLight,
    textAlign: 'right',
  },
  botTimeText: {
    color: colors.textLight,
    textAlign: 'left',
  },
  typingIndicator: {
    alignSelf: 'flex-start',
    marginVertical: 8,
    marginHorizontal: 20,
  },
  typingBubble: {
    backgroundColor: colors.coffeeCream,
    borderRadius: 20,
    borderBottomLeftRadius: 6,
    paddingHorizontal: 16,
    paddingVertical: 12,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  typingDots: {
    flexDirection: 'row',
    gap: 4,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.coffeeMedium,
  },
  dot1: {
    opacity: 0.4,
  },
  dot2: {
    opacity: 0.6,
  },
  dot3: {
    opacity: 0.8,
  },
  typingText: {
    fontSize: 14,
    color: colors.textSecondary,
    fontStyle: 'italic',
  },
  inputContainer: {
    position: 'absolute',
    bottom: 35,
    left: 0,
    right: 0,
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: 'transparent',
    zIndex: 3,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: colors.coffeeCream,
    borderRadius: 24,
    borderWidth: 1.5,
    borderColor: `${colors.coffeeMedium}20`,
    paddingHorizontal: 16,
    paddingVertical: 8,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 8,
    minHeight: 50,
    maxHeight: 120,
  },
  textInput: {
    flex: 1,
    fontSize: 16,
    color: colors.textPrimary,
    paddingVertical: 8,
    paddingRight: 8,
    textAlignVertical: 'center',
    lineHeight: 22,
  },
  sendButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.coffeeDark,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 8,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 4,
  },
  sendButtonDisabled: {
    backgroundColor: colors.coffeeLight,
    shadowOpacity: 0.1,
  },
  sendButtonText: {
    color: colors.coffeeWhite,
    fontSize: 18,
    fontWeight: '600',
  },
}); 