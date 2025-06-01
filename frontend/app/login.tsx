import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  Platform,
  Animated,
  Easing,
} from 'react-native';
import { useAuth } from '@/contexts/AuthContext';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';

const { width, height } = Dimensions.get('window');

// Steve Jobs-inspired Coffee color palette
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
  gradientStart: '#FFFEF7',
  gradientEnd: '#F5F5DC',
  buttonPrimary: '#4A3728',
  buttonSecondary: '#FFFFFF',
  success: '#8FBC8F',
  shadow: 'rgba(74, 55, 40, 0.15)',
};

// Elegant Coffee Character with Steve Jobs-level simplicity
const ElegantCoffeeCharacter = () => {
  const scaleAnim = React.useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    // Simple, elegant entrance
    Animated.timing(scaleAnim, {
      toValue: 1,
      duration: 800,
      easing: Easing.out(Easing.ease),
      useNativeDriver: true,
    }).start();
  }, []);

  return (
    <View style={styles.heroContainer}>
      <Animated.View 
        style={[
          styles.characterContainer,
          {
            transform: [{ scale: scaleAnim }],
          }
        ]}
      >
        <Image
          source={require('../assets/images/Coffy.png')}
          style={styles.characterImage}
          contentFit="contain"
          transition={300}
        />
      </Animated.View>
    </View>
  );
};

export default function CreateAccountScreen() {
  const { handleGoogleLogin, loading } = useAuth();
  const [contentAnim] = useState(new Animated.Value(0));

  useEffect(() => {
    // Simple, staggered entrance
    Animated.sequence([
      Animated.delay(400),
      Animated.timing(contentAnim, {
        toValue: 1,
        duration: 600,
        easing: Easing.out(Easing.ease),
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const handleLogin = async () => {
    try {
      await handleGoogleLogin();
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar style="dark" backgroundColor={colors.background} />
      
      {/* Gradient Background */}
      <LinearGradient
        colors={[colors.gradientStart, colors.gradientEnd]}
        style={styles.gradientBackground}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      />

      <View style={styles.content}>
        {/* Hero Section */}
        <ElegantCoffeeCharacter />

        {/* Content Section */}
        <Animated.View 
          style={[
            styles.textSection,
            {
              opacity: contentAnim,
              transform: [
                {
                  translateY: contentAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [20, 0],
                  }),
                },
              ],
            }
          ]}
        >
          <Text style={styles.brandTitle}>Welcome to Coffy</Text>
          <Text style={styles.subtitle}>
            Where every Coffy moment becomes a beautiful connection with friends
          </Text>
        </Animated.View>

        {/* Action Section */}
        <Animated.View 
          style={[
            styles.actionSection,
            {
              opacity: contentAnim,
              transform: [
                {
                  translateY: contentAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [20, 0],
                  }),
                },
              ],
            }
          ]}
        >
          {/* Primary CTA */}
          <TouchableOpacity
            style={[styles.primaryButton, loading && styles.primaryButtonLoading]}
            onPress={handleLogin}
            disabled={loading}
            activeOpacity={0.8}
          >
            <View style={styles.buttonContent}>
              <Ionicons 
                name="logo-google" 
                size={20} 
                color={colors.coffeeWhite} 
                style={styles.buttonIcon}
              />
              <Text style={styles.primaryButtonText}>
                {loading ? 'Creating your account...' : 'Continue with Google'}
              </Text>
            </View>
            {loading && (
              <Animated.View style={styles.loadingIndicator} />
            )}
          </TouchableOpacity>
        </Animated.View>

        {/* Legal Section */}
        <View style={styles.legalSection}>
          <Text style={styles.legalText}>
            By continuing, you agree to our{' '}
            <Text style={styles.legalLink}>Terms of Service</Text>
            {' '}and{' '}
            <Text style={styles.legalLink}>Privacy Policy</Text>
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  gradientBackground: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
    paddingTop: 60,
    paddingBottom: 40,
  },
  heroContainer: {
    width: 220,
    height: 220,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 50,
    position: 'relative',
  },
  characterContainer: {
    width: 180,
    height: 180,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 90,
    backgroundColor: colors.coffeeWhite,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.25,
    shadowRadius: 20,
    elevation: 12,
    overflow: 'hidden',
  },
  characterImage: {
    width: 160,
    height: 160,
    borderRadius: 80,
  },
  textSection: {
    alignItems: 'center',
    marginBottom: 50,
    paddingHorizontal: 20,
  },
  brandTitle: {
    fontSize: 32,
    fontWeight: '800',
    color: colors.coffeeDark,
    textAlign: 'center',
    marginBottom: 16,
    letterSpacing: -0.8,
    lineHeight: 38,
  },
  subtitle: {
    fontSize: 16,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
    fontWeight: '400',
    maxWidth: 280,
  },
  actionSection: {
    width: '100%',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  primaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.buttonPrimary,
    paddingVertical: 18,
    paddingHorizontal: 32,
    borderRadius: 16,
    width: '100%',
    maxWidth: 320,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 8,
    marginBottom: 36,
    position: 'relative',
    overflow: 'hidden',
  },
  primaryButtonLoading: {
    backgroundColor: colors.coffeeMedium,
    opacity: 0.8,
  },
  buttonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonIcon: {
    marginRight: 12,
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.coffeeWhite,
    letterSpacing: 0.3,
  },
  loadingIndicator: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(74, 55, 40, 0.3)',
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  legalSection: {
    alignItems: 'center',
    paddingHorizontal: 40,
    marginTop: 20,
  },
  legalText: {
    fontSize: 12,
    color: colors.textLight,
    textAlign: 'center',
    lineHeight: 18,
    fontWeight: '400',
  },
  legalLink: {
    fontWeight: '600',
    color: colors.coffeeMedium,
  },
}); 