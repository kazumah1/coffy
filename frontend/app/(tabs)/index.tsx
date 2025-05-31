import { Image } from 'expo-image';
import { Platform, StyleSheet, TouchableOpacity, Text } from 'react-native';
import { router } from 'expo-router';

import { HelloWave } from '@/components/HelloWave';
import ParallaxScrollView from '@/components/ParallaxScrollView';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import LoginButton from '@/components/LoginButton';
import Availability from '@/components/Availability';
import { useAuth } from '@/contexts/AuthContext';

export default function HomeScreen() {
  const { user, signOut } = useAuth();

  const navigateToChat = () => {
    router.push('/chat');
  };

  return (
    <ThemedView style={styles.container}>
      <ThemedView style={styles.welcomeContainer}>
        <ThemedText style={styles.welcomeText}>
          Welcome to CoffyChat! ☕
        </ThemedText>
        {user && (
          <ThemedText style={styles.userText}>
            Hello, {user.name || user.email}!
          </ThemedText>
        )}
      </ThemedView>
      
      <LoginButton />
      <Availability start="2025-05-26T17:00:00-07:00" end="2025-05-31T17:00:00-07:00" />
      
      {user && (
        <TouchableOpacity style={styles.chatButton} onPress={navigateToChat}>
          <Image 
            source={require('@/assets/images/coffee-hello.png')} 
            style={styles.coffeeIcon}
            contentFit="contain"
          />
          <Text style={styles.chatButtonText}>Chat with Mr. Coffee</Text>
        </TouchableOpacity>
      )}
      
      {user && (
        <TouchableOpacity style={styles.signOutButton} onPress={signOut}>
          <Text style={styles.signOutText}>Sign Out</Text>
        </TouchableOpacity>
      )}
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  welcomeContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  welcomeText: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
  },
  userText: {
    fontSize: 16,
    textAlign: 'center',
    opacity: 0.8,
  },
  chatButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 20,
    paddingVertical: 15,
    paddingHorizontal: 25,
    backgroundColor: '#8B4513',
    borderRadius: 25,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  coffeeIcon: {
    width: 30,
    height: 30,
    marginRight: 10,
  },
  chatButtonText: {
    color: '#FFEFCC',
    fontWeight: '600',
    fontSize: 16,
  },
  signOutButton: {
    marginTop: 20,
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: '#FF6B6B',
    borderRadius: 8,
  },
  signOutText: {
    color: 'white',
    fontWeight: '600',
    fontSize: 16,
  },
  stepContainer: {
    gap: 8,
    marginBottom: 8,
  },
  reactLogo: {
    height: 178,
    width: 290,
    bottom: 0,
    left: 0,
    position: 'absolute',
  },
});
