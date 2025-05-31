import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  Platform,
} from 'react-native';
import { useAuth } from '@/contexts/AuthContext';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import { Image } from 'expo-image';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  withSequence,
} from 'react-native-reanimated';

const { width, height } = Dimensions.get('window');

// Coffee Character Component with Animation
const CoffeeCharacter = () => {
  const coffeeScale = useSharedValue(1);
  const rotation = useSharedValue(0);

  React.useEffect(() => {
    // Gentle bounce animation
    coffeeScale.value = withRepeat(
      withSequence(
        withTiming(1.05, { duration: 2000 }),
        withTiming(1, { duration: 2000 })
      ),
      -1,
      true
    );

    // Subtle rotation animation
    rotation.value = withRepeat(
      withSequence(
        withTiming(2, { duration: 3000 }),
        withTiming(-2, { duration: 3000 }),
        withTiming(0, { duration: 3000 })
      ),
      -1,
      true
    );
  }, []);

  const animatedStyle = useAnimatedStyle(() => {
    return {
      transform: [
        { scale: coffeeScale.value },
        { rotate: `${rotation.value}deg` }
      ],
    };
  });

  return (
    <View style={styles.coffeeContainer}>
      <Animated.View style={[styles.coffeeImageContainer, animatedStyle]}>
        <Image
          source={require('../assets/images/coffee-character.png')}
          style={styles.coffeeImage}
          contentFit="contain"
          placeholder="☕"
          transition={200}
        />
      </Animated.View>
    </View>
  );
};

export default function LoginScreen() {
  const { handleGoogleLogin, loading } = useAuth();

  const handleLogin = async () => {
    try {
      await handleGoogleLogin();
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar style="dark" />
      
      <View style={styles.content}>
        {/* Coffee Character Illustration */}
        <CoffeeCharacter />

        {/* Title and Subtitle */}
        <View style={styles.textContainer}>
          <Text style={styles.title}>Create an account</Text>
          <Text style={styles.subtitle}>Enter your email to sign up for this app</Text>
        </View>

        {/* Google Login Button */}
        <TouchableOpacity
          style={styles.googleButton}
          onPress={handleLogin}
          disabled={loading}
        >
          <Ionicons name="logo-google" size={20} color="#4285F4" />
          <Text style={styles.googleButtonText}>
            {loading ? 'Signing in...' : 'Continue with Google'}
          </Text>
        </TouchableOpacity>

        {/* Terms and Privacy */}
        <View style={styles.legalContainer}>
          <Text style={styles.legalText}>
            By clicking continue, you agree to our{' '}
            <Text style={styles.legalLink}>Terms of Service</Text>
            {'\n'}and <Text style={styles.legalLink}>Privacy Policy</Text>
          </Text>
        </View>
      </View>

      {/* Bottom indicator */}
      <View style={styles.bottomIndicator} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5E6D3',
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  coffeeContainer: {
    width: 280,
    height: 280,
    marginBottom: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  coffeeImageContainer: {
    width: '100%',
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
  },
  coffeeImage: {
    width: '100%',
    height: '100%',
  },
  textContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#3D2914',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#6B4423',
    textAlign: 'center',
    lineHeight: 22,
    opacity: 0.9,
  },
  googleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    width: '100%',
    maxWidth: 300,
    shadowColor: '#8B4513',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 6,
    elevation: 4,
    marginBottom: 32,
    borderWidth: 1,
    borderColor: 'rgba(139, 69, 19, 0.1)',
  },
  googleButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#3D2914',
    marginLeft: 12,
  },
  legalContainer: {
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  legalText: {
    fontSize: 12,
    color: '#8B6F47',
    textAlign: 'center',
    lineHeight: 18,
    opacity: 0.8,
  },
  legalLink: {
    fontWeight: '600',
    color: '#6B4423',
  },
  bottomIndicator: {
    position: 'absolute',
    bottom: 8,
    left: '50%',
    marginLeft: -67.5,
    width: 135,
    height: 5,
    backgroundColor: '#8B4513',
    borderRadius: 3,
    opacity: 0.4,
  },
}); 