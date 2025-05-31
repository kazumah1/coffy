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
  Dimensions
} from 'react-native';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useAuth } from '@/contexts/AuthContext';

const { width, height } = Dimensions.get('window');

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

const BACKEND_URL = "http://localhost:8000";

export default function ChatScreen() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Hi',
      isUser: false,
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);

  const sendMessage = async () => {
    if (!inputText.trim() || !user) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText.trim(),
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/llm/prompt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          request: userMessage.text,
          creator_id: user.id || user.email
        }),
      });

      const data = await response.json();
      
      // Extract the actual response text from the nested structure
      let responseText = 'Sorry, I encountered an error. Please try again.';
      if (data && data.response) {
        // Check if response has content (OpenAI format)
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
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I encountered an error. Please try again.',
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
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

  const addSampleMessage = () => {
    const sampleMessage: Message = {
      id: Date.now().toString(),
      text: 'You just edit any text to type in the conversation you want to show, and delete any bubbles you don\'t want to use',
      isUser: false,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, sampleMessage]);
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#F5E6D3" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Chat</Text>
        <TouchableOpacity style={styles.backButton} onPress={goBack}>
          <Text style={styles.backButtonText}>←</Text>
        </TouchableOpacity>
      </View>

      {/* Chat Area */}
      <View style={styles.chatContainer}>
        {/* Coffee Character */}
        <View style={styles.characterContainer}>
          <Image 
            source={require('@/assets/images/coffee-hello.png')} 
            style={styles.coffeeCharacter}
            contentFit="contain"
          />
        </View>

        {/* Messages */}
        <ScrollView 
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
          showsVerticalScrollIndicator={false}
        >
          {messages.map((message) => (
            <View
              key={message.id}
              style={[
                styles.messageBubble,
                message.isUser ? styles.userBubble : styles.botBubble
              ]}
            >
              <Text style={[
                styles.messageText,
                message.isUser ? styles.userText : styles.botText
              ]}>
                {message.text}
              </Text>
            </View>
          ))}
          
          {/* Sample message button */}
          <TouchableOpacity style={styles.sampleButton} onPress={addSampleMessage}>
            <Text style={styles.sampleButtonText}>Boom!</Text>
          </TouchableOpacity>
          
          {isLoading && (
            <View style={styles.typingIndicator}>
              <Text style={styles.typingText}>Mr. Coffee is typing...</Text>
            </View>
          )}
        </ScrollView>

        {/* Input Area */}
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.inputContainer}
        >
          <View style={styles.inputRow}>
            <View style={styles.inputWrapper}>
              <Text style={styles.inputIcon}>☕</Text>
              <TextInput
                style={styles.textInput}
                value={inputText}
                onChangeText={setInputText}
                placeholder="Message LLM..."
                placeholderTextColor="#8B4513"
                multiline
                maxLength={500}
              />
            </View>
            <TouchableOpacity 
              style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]} 
              onPress={sendMessage}
              disabled={!inputText.trim() || isLoading}
            >
              <Text style={styles.sendButtonText}>→</Text>
            </TouchableOpacity>
          </View>
        </KeyboardAvoidingView>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5E6D3',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 50,
    paddingBottom: 10,
    paddingHorizontal: 20,
    backgroundColor: '#8B4513',
    position: 'relative',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#F5E6D3',
  },
  backButton: {
    position: 'absolute',
    left: 20,
    top: 50,
    padding: 5,
  },
  backButtonText: {
    fontSize: 24,
    color: '#F5E6D3',
    fontWeight: 'bold',
  },
  chatContainer: {
    flex: 1,
    backgroundColor: '#F5E6D3',
  },
  characterContainer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  coffeeCharacter: {
    width: 200,
    height: 200,
  },
  messagesContainer: {
    flex: 1,
    paddingHorizontal: 20,
  },
  messagesContent: {
    paddingBottom: 20,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 15,
    marginVertical: 5,
    borderRadius: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  userBubble: {
    backgroundColor: '#FFFFFF',
    alignSelf: 'flex-end',
    borderBottomRightRadius: 5,
  },
  botBubble: {
    backgroundColor: '#8B4513',
    alignSelf: 'flex-start',
    borderBottomLeftRadius: 5,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 20,
  },
  userText: {
    color: '#333333',
  },
  botText: {
    color: '#F5E6D3',
  },
  sampleButton: {
    backgroundColor: '#8B4513',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 20,
    alignSelf: 'flex-start',
    marginVertical: 10,
  },
  sampleButtonText: {
    color: '#F5E6D3',
    fontWeight: '600',
    fontSize: 16,
  },
  typingIndicator: {
    alignSelf: 'flex-start',
    paddingVertical: 10,
  },
  typingText: {
    color: '#8B4513',
    fontStyle: 'italic',
  },
  inputContainer: {
    backgroundColor: '#F5E6D3',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderTopWidth: 1,
    borderTopColor: '#D4B896',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 10,
  },
  inputWrapper: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#8B4513',
    borderRadius: 25,
    paddingHorizontal: 15,
    paddingVertical: 8,
    minHeight: 50,
  },
  inputIcon: {
    fontSize: 20,
    marginRight: 10,
  },
  textInput: {
    flex: 1,
    fontSize: 16,
    color: '#F5E6D3',
    maxHeight: 100,
    textAlignVertical: 'center',
  },
  sendButton: {
    backgroundColor: '#8B4513',
    width: 50,
    height: 50,
    borderRadius: 25,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
  sendButtonText: {
    color: '#F5E6D3',
    fontSize: 20,
    fontWeight: 'bold',
  },
}); 