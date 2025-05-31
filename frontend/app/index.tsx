import React, { useState } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'expo-router';
import LoginScreen from './login';
import SplashScreen from './splash';

export default function IndexScreen() {
  const { user, loading } = useAuth();
  const [showSplash, setShowSplash] = useState(true);
  const router = useRouter();

  const handleSplashComplete = () => {
    setShowSplash(false);
  };

  // Show loading spinner while auth is initializing
  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F5E6D3' }}>
        <ActivityIndicator size="large" color="#8B4513" />
      </View>
    );
  }

  // If user is authenticated, navigate to main app
  if (user && !showSplash) {
    router.replace('/(tabs)');
    return null;
  }

  // Show splash screen first
  if (showSplash) {
    return <SplashScreen onAnimationComplete={handleSplashComplete} />;
  }

  // Show login screen if not authenticated
  return <LoginScreen />;
} 