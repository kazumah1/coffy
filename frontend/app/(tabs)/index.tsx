import React from 'react';
import { 
  View, 
  Text, 
  TouchableOpacity, 
  StyleSheet, 
  StatusBar,
  ScrollView,
  Dimensions,
  SafeAreaView,
  Animated
} from 'react-native';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useAuth } from '@/contexts/AuthContext';

const { width } = Dimensions.get('window');

// Coffee-themed color palette (same as chat)
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

export default function HomeScreen() {
  const { user, signOut } = useAuth();

  const navigateToChat = () => {
    router.push('/chat');
  };

  const navigateToProfile = () => {
    router.push('/profile');
  };

  const navigateToContacts = () => {
    router.push('/contacts');
  };

  const navigateToBestFriends = () => {
    router.push('/best-friends');
  };

  // Quick action prompts
  const navigateToChatWithPrompt = (prompt: string) => {
    router.push({
      pathname: '/chat',
      params: { autoPrompt: prompt }
    });
  };

  const planCoffyPrompt = "Hi Joe! I'd like to plan a Coffy meetup with my friends sometime this week. Could you help me coordinate this? Please use a semi-casual tone when reaching out to everyone. Find a time that works for most people and suggest a nice Coffy spot. Thanks!";

  const scheduleDinnerPrompt = "Hey Joe, I want to schedule a dinner with my friend group sometime this week after 5:00 PM. Could you help coordinate this? Please use a semi-formal tone when sending messages to everyone. Look for a time that works for the group and maybe suggest some restaurant options. Thank you!";

  const setMeetingPrompt = "Hi Joe! I need to set up a meeting with my team. Can you help coordinate this and find a time that works for everyone? Please use a casual tone when reaching out. Thanks for your help!";

  const planEventPrompt = "Hey Joe! I want to plan a fun event with my friends. Could you help me organize something exciting? Use a casual and enthusiastic tone when messaging everyone. Thanks!";

  const [fadeAnim, setFadeAnim] = React.useState(new Animated.Value(1));
  const [scaleAnim, setScaleAnim] = React.useState(new Animated.Value(1));
  const [slideAnim, setSlideAnim] = React.useState(new Animated.Value(0));

  const handlePress = () => {
    Animated.sequence([
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 500,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 1.1,
        duration: 500,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 20,
        duration: 1000,
        useNativeDriver: true,
      })
    ]).start(() => {
      // Reset animation
      setFadeAnim(new Animated.Value(1));
      setScaleAnim(new Animated.Value(1));
      setSlideAnim(new Animated.Value(0));
    });
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.background} />
      
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.logoContainer}>
          <View style={styles.coffeeLogo}>
            <Image 
              source={require('@/assets/images/coffee-character.png')} 
              style={styles.logoImage}
              contentFit="cover"
            />
          </View>
          <Text style={styles.appName}>Coffy</Text>
        </View>
        
        {user && (
          <TouchableOpacity style={styles.profileButton} onPress={navigateToProfile}>
            <Text style={styles.profileText}>👤</Text>
          </TouchableOpacity>
        )}
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Welcome Section */}
        <View style={styles.welcomeSection}>
          <Text style={styles.welcomeTitle}>
            Welcome back{user?.name ? `, ${user.name.split(' ')[0]}` : ''}!
          </Text>
          <Text style={styles.welcomeSubtitle}>
            Ready to grab Coffy with your friends?
          </Text>
        </View>

        {/* Main Actions */}
        <View style={styles.actionsContainer}>
          <TouchableOpacity style={styles.primaryAction} onPress={navigateToChat}>
            <View style={styles.actionIcon}>
              <Image 
                source={require('@/assets/images/coffee-character.png')} 
                style={styles.actionImage}
                contentFit="contain"
              />
            </View>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Chat with Joe</Text>
              <Text style={styles.actionSubtitle}>Plan your next Coffy meetup</Text>
            </View>
            <Text style={styles.actionArrow}>→</Text>
          </TouchableOpacity>

          <View style={styles.secondaryActions}>
            <TouchableOpacity style={styles.secondaryAction} onPress={navigateToContacts}>
              <View style={styles.secondaryIcon}>
                <Text style={styles.secondaryIconText}>📱</Text>
              </View>
              <View style={styles.secondaryContent}>
                <Text style={styles.secondaryTitle}>Contacts</Text>
                <Text style={styles.secondarySubtitle}>Manage your friends</Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity style={styles.secondaryAction} onPress={navigateToBestFriends}>
              <View style={styles.secondaryIcon}>
                <Text style={styles.secondaryIconText}>⭐</Text>
              </View>
              <View style={styles.secondaryContent}>
                <Text style={styles.secondaryTitle}>Best Friends</Text>
                <Text style={styles.secondarySubtitle}>Your inner circle</Text>
              </View>
            </TouchableOpacity>
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.suggestionsSection}>
          <Text style={styles.suggestionsTitle}>Quick Actions</Text>
          <View style={styles.suggestionsGrid}>
            <TouchableOpacity 
              style={styles.suggestionCard} 
              onPress={() => navigateToChatWithPrompt(planCoffyPrompt)}
            >
              <Text style={styles.suggestionEmoji}>☕</Text>
              <Text style={styles.suggestionText}>Plan Coffy</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.suggestionCard} 
              onPress={() => navigateToChatWithPrompt(scheduleDinnerPrompt)}
            >
              <Text style={styles.suggestionEmoji}>🍽️</Text>
              <Text style={styles.suggestionText}>Schedule Dinner</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.suggestionCard} 
              onPress={() => navigateToChatWithPrompt(setMeetingPrompt)}
            >
              <Text style={styles.suggestionEmoji}>📅</Text>
              <Text style={styles.suggestionText}>Set Meeting</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.suggestionCard} 
              onPress={() => navigateToChatWithPrompt(planEventPrompt)}
            >
              <Text style={styles.suggestionEmoji}>🎉</Text>
              <Text style={styles.suggestionText}>Plan Event</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Coffee Radar - Revolutionary Feature
        <Animated.View 
          style={[
            styles.radarContainer,
            {
              opacity: fadeAnim,
              transform: [
                { scale: scaleAnim },
                { translateY: slideAnim }
              ],
            },
          ]}
        >
          <TouchableOpacity 
            style={styles.radarCard}
            onPress={() => router.push('/coffee-radar')}
            activeOpacity={0.9}
          >
            <View style={styles.radarHeader}>
              <Text style={styles.radarTitle}>☕ Coffy Radar</Text>
              <Text style={styles.radarSubtitle}>See who's available right now</Text>
            </View>
            
            Mini Radar Preview
            <View style={styles.miniRadar}>
              <View style={styles.radarCircle}>
                Radar rings
                <View style={[styles.radarRing, { width: 80, height: 80 }]} />
                <View style={[styles.radarRing, { width: 60, height: 60 }]} />
                <View style={[styles.radarRing, { width: 40, height: 40 }]} />
                
                Center dot
                <View style={styles.radarCenter}>
                </View>
                
                Sample availability dots
                <View style={[styles.availabilityDot, styles.available, { top: 15, right: 20 }]} />
                <View style={[styles.availabilityDot, styles.maybe, { bottom: 25, left: 15 }]} />
                <View style={[styles.availabilityDot, styles.busy, { top: 35, left: 35 }]} />
                <View style={[styles.availabilityDot, styles.available, { bottom: 15, right: 25 }]} />
              </View>
              
              <View style={styles.radarStats}>
                <Text style={styles.radarStatsText}>3 friends available</Text>
                <Text style={styles.radarStatsSubtext}>Perfect weather for outdoor Coffy</Text>
              </View>
            </View>

            <View style={styles.radarAction}>
              <Text style={styles.radarActionText}>Tap to coordinate instant Coffy →</Text>
            </View>
          </TouchableOpacity>
        </Animated.View> */}
      </ScrollView>
    </SafeAreaView>
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
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: `${colors.coffeeMedium}10`,
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
    fontSize: 22,
    fontWeight: '700',
    color: colors.coffeeDark,
    letterSpacing: -0.5,
  },
  profileButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.coffeeCream,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  profileText: {
    fontSize: 18,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  welcomeSection: {
    paddingVertical: 30,
    alignItems: 'center',
  },
  welcomeTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: colors.coffeeDark,
    textAlign: 'center',
    marginBottom: 8,
    letterSpacing: -0.5,
  },
  welcomeSubtitle: {
    fontSize: 16,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
  },
  actionsContainer: {
    gap: 20,
    marginBottom: 40,
  },
  primaryAction: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.coffeeCream,
    borderRadius: 20,
    padding: 20,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
    borderWidth: 1,
    borderColor: `${colors.coffeeMedium}15`,
  },
  actionIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: colors.coffeeMedium,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
    overflow: 'hidden',
  },
  actionImage: {
    width: 50,
    height: 50,
    borderRadius: 25,
  },
  actionContent: {
    flex: 1,
  },
  actionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.coffeeDark,
    marginBottom: 4,
  },
  actionSubtitle: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  actionArrow: {
    fontSize: 24,
    color: colors.coffeeMedium,
    fontWeight: '600',
  },
  secondaryActions: {
    flexDirection: 'row',
    gap: 12,
  },
  secondaryAction: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.background,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1.5,
    borderColor: `${colors.coffeeMedium}20`,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  secondaryIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.coffeeCream,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  secondaryIconText: {
    fontSize: 18,
  },
  secondaryContent: {
    flex: 1,
  },
  secondaryTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.coffeeDark,
    marginBottom: 2,
  },
  secondarySubtitle: {
    fontSize: 12,
    color: colors.textLight,
  },
  suggestionsSection: {
    marginBottom: 40,
  },
  suggestionsTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.coffeeDark,
    marginBottom: 16,
  },
  suggestionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  suggestionCard: {
    width: (width - 56) / 2,
    backgroundColor: colors.background,
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: `${colors.coffeeMedium}20`,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  suggestionEmoji: {
    fontSize: 32,
    marginBottom: 8,
  },
  suggestionText: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.textPrimary,
    textAlign: 'center',
  },
  radarContainer: {
    marginBottom: 40,
  },
  radarCard: {
    backgroundColor: colors.background,
    borderRadius: 16,
    padding: 20,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  radarHeader: {
    alignItems: 'center',
    marginBottom: 16,
  },
  radarTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.coffeeDark,
    marginBottom: 4,
  },
  radarSubtitle: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  miniRadar: {
    alignItems: 'center',
    marginBottom: 16,
  },
  radarCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'transparent',
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  radarRing: {
    position: 'absolute',
    borderWidth: 1,
    borderColor: `${colors.coffeeMedium}40`,
    borderRadius: 50,
  },
  radarCenter: {
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: colors.coffeeDark,
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
  },
  radarStats: {
    alignItems: 'center',
  },
  radarStatsText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.coffeeDark,
    marginBottom: 4,
  },
  radarStatsSubtext: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  radarAction: {
    alignItems: 'center',
    marginTop: 16,
  },
  radarActionText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.coffeeMedium,
  },
  availabilityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    position: 'absolute',
  },
  available: {
    backgroundColor: '#4CAF50',
  },
  maybe: {
    backgroundColor: '#FF9800',
  },
  busy: {
    backgroundColor: '#F44336',
  },
});
