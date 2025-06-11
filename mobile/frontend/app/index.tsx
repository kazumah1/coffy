import React, { useState, useEffect } from 'react';
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

  // Handle navigation when user is authenticated and splash is complete
  useEffect(() => {
    if (user && !loading) {
      if (user.needsProfileSetup) {
        router.replace('/profile-setup');
      } else {
        router.replace('/(tabs)');
      }
    }
  }, [user, showSplash, loading, router]);

  // Show loading spinner while auth is initializing
  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F5E6D3' }}>
        <ActivityIndicator size="large" color="#8B4513" />
      </View>
    );
  }

  // If user is authenticated, show loading while navigating
  if (user && !showSplash) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F5E6D3' }}>
        <ActivityIndicator size="large" color="#8B4513" />
      </View>
    );
  }


  // Show login screen if not authenticated
  return <LoginScreen />;
} 