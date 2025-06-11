import React, { useEffect } from 'react';
import {
  View,
  StyleSheet,
  Dimensions,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Image } from 'expo-image';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
} from 'react-native-reanimated';

const { width, height } = Dimensions.get('window');

interface SplashScreenProps {
  onAnimationComplete: () => void;
}

export default function SplashScreen({ onAnimationComplete }: SplashScreenProps) {
  const fadeIn = useSharedValue(0);

  useEffect(() => {
    // Quick fade-in animation
    fadeIn.value = withTiming(1, { duration: 300 });

    // Auto-transition after GIF duration (5.5 seconds)
    const timer = setTimeout(() => {
      onAnimationComplete();
    }, 5500); // 5.5 seconds - full GIF duration

    return () => clearTimeout(timer);
  }, []);

  const animatedStyle = useAnimatedStyle(() => {
    return {
      opacity: fadeIn.value,
    };
  });

  return (
    <View style={styles.container}>
      <StatusBar style="light" backgroundColor="transparent" translucent />
      
      <Animated.View style={[styles.fullScreenContainer, animatedStyle]}>
        {/* Your GIF Animation - Very Zoomed In */}
        <Image
          source={require('../assets/images/splash-animation.gif')}
          style={styles.fullScreenGif}
          contentFit="cover" // Back to cover for very zoomed in effect
        />
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000', // Black background that blends with most GIFs
  },
  fullScreenContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    width: width,
    height: height,
  },
  fullScreenGif: {
    width: '100%',
    height: '100%',
  },
}); 