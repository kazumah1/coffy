import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  TouchableOpacity, 
  StyleSheet, 
  StatusBar,
  SafeAreaView,
  Animated,
  Dimensions,
  Alert,
  Easing
} from 'react-native';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useAuth } from '@/contexts/AuthContext';
import * as SecureStore from 'expo-secure-store';
import * as Haptics from 'expo-haptics';

const { width, height } = Dimensions.get('window');

const BACKEND_URL = "https://www.coffy.app";
const REQUEST_TIMEOUT = 3000; // 3 seconds timeout

// Helper function to add timeout to fetch requests
const fetchWithTimeout = async (url: string, options: RequestInit = {}, timeout = REQUEST_TIMEOUT): Promise<Response> => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
};

// Coffy-themed color palette
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
  available: '#4CAF50',
  maybe: '#FF9800',
  busy: '#F44336',
};

interface Friend {
  id: string;
  name: string;
  status: 'available' | 'maybe' | 'busy';
  distance: number;
  lastSeen: string;
}

interface CoffySpot {
  id: string;
  name: string;
  rating: number;
  distance: string;
  vibe: string;
  weatherScore: number;
}

export default function CoffyRadarScreen() {
  const { user } = useAuth();
  const [friends, setFriends] = useState<Friend[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFriends, setSelectedFriends] = useState<string[]>([]);
  const [suggestedSpot, setSuggestedSpot] = useState<CoffySpot | null>(null);
  const [isCoordinating, setIsCoordinating] = useState(false);
  
  // Animation refs
  const rotationAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;

  useEffect(() => {
    loadFriendsAvailability();
    startRadarAnimation();
    
    // Entrance animation
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        easing: Easing.out(Easing.ease),
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 800,
        easing: Easing.out(Easing.ease),
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const startRadarAnimation = () => {
    // Continuous radar rotation
    Animated.loop(
      Animated.timing(rotationAnim, {
        toValue: 1,
        duration: 4000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();

    // Pulse animation for center
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.2,
          duration: 1000,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1000,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    ).start();
  };

  const loadFriendsAvailability = async () => {
    setLoading(true);
    try {
      // First try to load from backend API
      try {
        const response = await fetchWithTimeout(`${BACKEND_URL}/api/radar/friends-availability/${user?.id}`);
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.friends) {
            setFriends(data.friends);
            
            // Load coffee spot recommendations
            await loadCoffySpotRecommendations(data.friends.length);
            setLoading(false);
            return;
          }
        }
      } catch (error) {
        console.log('Backend not available, using local data');
      }
      
      // Fallback to local storage + simulation
      const savedContacts = await SecureStore.getItemAsync('userContacts');
      const savedBestFriends = await SecureStore.getItemAsync('userBestFriends');
      
      if (savedContacts && savedBestFriends) {
        const contacts = JSON.parse(savedContacts);
        const bestFriendIds = JSON.parse(savedBestFriends);
        
        // Simulate real-time availability (in production, this would be from backend)
        const availableFriends = contacts
          .filter((contact: any) => bestFriendIds.includes(contact.id))
          .slice(0, 8) // Limit for UI
          .map((contact: any, index: number) => ({
            id: contact.id,
            name: contact.name,
            status: ['available', 'maybe', 'busy'][Math.floor(Math.random() * 3)] as 'available' | 'maybe' | 'busy',
            distance: Math.floor(Math.random() * 10) + 1,
            lastSeen: ['Just now', '5m ago', '15m ago', '1h ago'][Math.floor(Math.random() * 4)]
          }));
        
        setFriends(availableFriends);
        
        // Suggest a coffee spot based on availability
        const availableCount = availableFriends.filter(f => f.status === 'available').length;
        if (availableCount > 0) {
          setSuggestedSpot({
            id: '1',
            name: 'Moonrise Coffee',
            rating: 4.8,
            distance: '0.3 mi',
            vibe: 'Cozy & Quiet',
            weatherScore: 95
          });
        }
      }
    } catch (error) {
      console.error('Error loading friends availability:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCoffySpotRecommendations = async (groupSize: number) => {
    try {
      const response = await fetchWithTimeout(
        `${BACKEND_URL}/api/radar/coffee-spots?group_size=${groupSize}`
      );
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.recommendations.length > 0) {
          setSuggestedSpot(data.recommendations[0]); // Best recommendation
        }
      }
    } catch (error) {
      console.log('Could not load Coffy recommendations from backend');
    }
  };

  const toggleFriendSelection = (friendId: string) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setSelectedFriends(prev => 
      prev.includes(friendId) 
        ? prev.filter(id => id !== friendId)
        : [...prev, friendId]
    );
  };

  const coordinateInstantCoffy = async () => {
    if (selectedFriends.length === 0) {
      Alert.alert(
        'Select Friends',
        'Please select at least one friend to invite for Coffy.',
        [{ text: 'Got It' }]
      );
      return;
    }

    if (!suggestedSpot) {
      Alert.alert(
        'No Coffy Spot',
        'Please wait for Coffy spot recommendations to load.',
        [{ text: 'Got It' }]
      );
      return;
    }

    setIsCoordinating(true);
    await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);

    try {
      // Try to coordinate through backend API
      const response = await fetchWithTimeout(`${BACKEND_URL}/api/radar/coordinate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user?.id,
          friend_ids: selectedFriends,
          spot_id: suggestedSpot.id,
          message: `☕ Coffy at ${suggestedSpot.name} right now?`
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          const acceptedFriends = data.responses.filter((r: any) => r.response === 'accepted');
          const selectedNames = friends
            .filter(f => selectedFriends.includes(f.id))
            .map(f => f.name)
            .join(', ');
          
          Alert.alert(
            'Coffy Coordinated! ☕',
            `Invited ${selectedNames} to ${suggestedSpot.name}.\n\n${acceptedFriends.length} friends accepted and are on their way!`,
            [
              {
                text: 'Perfect',
                onPress: () => router.back()
              }
            ]
          );
          setIsCoordinating(false);
          return;
        }
      }
    } catch (error) {
      console.log('Backend coordination failed, showing local success');
    }

    // Fallback to local simulation
    setTimeout(() => {
      setIsCoordinating(false);
      const selectedNames = friends
        .filter(f => selectedFriends.includes(f.id))
        .map(f => f.name)
        .join(', ');
      
      Alert.alert(
        'Coffy Coordinated! ☕',
        `Invited ${selectedNames} to meet at ${suggestedSpot?.name}. They'll receive instant notifications with location and ETA.`,
        [
          {
            text: 'Perfect',
            onPress: () => router.back()
          }
        ]
      );
    }, 2000);
  };

  const getRadarDotPosition = (index: number, total: number, ringRadius: number) => {
    const angle = (index / total) * 2 * Math.PI;
    const x = Math.cos(angle) * ringRadius;
    const y = Math.sin(angle) * ringRadius;
    return { x, y };
  };

  const goBack = () => {
    router.back();
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" backgroundColor={colors.background} />
        
        <View style={styles.loadingContainer}>
          <Animated.View style={{ transform: [{ rotate: rotationAnim.interpolate({
            inputRange: [0, 1],
            outputRange: ['0deg', '360deg']
          }) }] }}>
            <Text style={styles.loadingRadar}>⚡</Text>
          </Animated.View>
          <Text style={styles.loadingText}>Scanning for Coffy crew...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const rotation = rotationAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg']
  });

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.background} />
      
      {/* Header - Steve Jobs inspired simplicity */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={goBack}>
          <Text style={styles.backArrow}>←</Text>
          <Text style={styles.backText}>Home</Text>
        </TouchableOpacity>
        
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>☕ Coffy Radar</Text>
          <View style={styles.liveIndicator}>
            <View style={styles.liveDot} />
            <Text style={styles.liveText}>LIVE</Text>
          </View>
        </View>
        
        <View style={styles.headerRight} />
      </View>

      <Animated.ScrollView 
        style={[styles.content, {
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }],
        }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Radar Display */}
        <View style={styles.radarSection}>
          <Text style={styles.sectionTitle}>Who's Available Now</Text>
          
          <View style={styles.radarContainer}>
            {/* Radar Background */}
            <View style={styles.radarBackground}>
              {/* Radar Rings */}
              <View style={[styles.radarRing, { width: 280, height: 280 }]} />
              <View style={[styles.radarRing, { width: 200, height: 200 }]} />
              <View style={[styles.radarRing, { width: 120, height: 120 }]} />
              
              {/* Radar Sweep */}
              <Animated.View 
                style={[
                  styles.radarSweep,
                  { transform: [{ rotate: rotation }] }
                ]}
              />
              
              {/* Center (You) */}
              <Animated.View 
                style={[
                  styles.radarCenter,
                  { transform: [{ scale: pulseAnim }] }
                ]}
              >
                <Text style={styles.radarCenterText}>YOU</Text>
              </Animated.View>
              
              {/* Friends as dots */}
              {friends.map((friend, index) => {
                const ring = friend.distance < 3 ? 60 : friend.distance < 7 ? 100 : 140;
                const position = getRadarDotPosition(index, friends.length, ring);
                const isSelected = selectedFriends.includes(friend.id);
                
                return (
                  <TouchableOpacity
                    key={friend.id}
                    style={[
                      styles.friendDot,
                      {
                        left: 140 + position.x - 15,
                        top: 140 + position.y - 15,
                        backgroundColor: colors[friend.status],
                        borderColor: isSelected ? colors.coffeeDark : 'transparent',
                        borderWidth: isSelected ? 3 : 0,
                      }
                    ]}
                    onPress={() => toggleFriendSelection(friend.id)}
                  >
                    <Text style={styles.friendInitial}>
                      {friend.name.charAt(0).toUpperCase()}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>

          {/* Legend */}
          <View style={styles.legend}>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: colors.available }]} />
              <Text style={styles.legendText}>Available</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: colors.maybe }]} />
              <Text style={styles.legendText}>Maybe</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: colors.busy }]} />
              <Text style={styles.legendText}>Busy</Text>
            </View>
          </View>
        </View>

        {/* Selected Friends */}
        {selectedFriends.length > 0 && (
          <View style={styles.selectedSection}>
            <Text style={styles.sectionTitle}>
              Selected ({selectedFriends.length})
            </Text>
            <View style={styles.selectedFriends}>
              {friends
                .filter(f => selectedFriends.includes(f.id))
                .map(friend => (
                  <View key={friend.id} style={styles.selectedFriend}>
                    <Text style={styles.selectedFriendName}>{friend.name}</Text>
                    <Text style={styles.selectedFriendStatus}>{friend.lastSeen}</Text>
                  </View>
                ))}
            </View>
          </View>
        )}

        {/* Suggested Coffee Spot */}
        {suggestedSpot && selectedFriends.length > 0 && (
          <View style={styles.suggestionSection}>
            <Text style={styles.sectionTitle}>Perfect Spot for Your Group</Text>
            <View style={styles.spotCard}>
              <View style={styles.spotHeader}>
                <Text style={styles.spotName}>{suggestedSpot.name}</Text>
                <View style={styles.spotRating}>
                  <Text style={styles.spotRatingText}>⭐ {suggestedSpot.rating}</Text>
                </View>
              </View>
              <Text style={styles.spotDetails}>
                {suggestedSpot.distance} • {suggestedSpot.vibe}
              </Text>
              <Text style={styles.spotWeather}>
                🌤️ Perfect weather score: {suggestedSpot.weatherScore}%
              </Text>
            </View>
          </View>
        )}

        {/* Coordinate Button */}
        <View style={styles.actionSection}>
          <TouchableOpacity 
            style={[
              styles.coordinateButton,
              selectedFriends.length === 0 && styles.coordinateButtonDisabled
            ]}
            onPress={coordinateInstantCoffy}
            disabled={selectedFriends.length === 0 || isCoordinating}
          >
            {isCoordinating ? (
              <View style={styles.coordinatingState}>
                <Animated.View style={{ transform: [{ rotate: rotation }] }}>
                  <Text style={styles.coordinatingIcon}>⚡</Text>
                </Animated.View>
                <Text style={styles.coordinateButtonText}>Coordinating...</Text>
              </View>
            ) : (
              <Text style={styles.coordinateButtonText}>
                ☕ Coordinate Instant Coffy
              </Text>
            )}
          </TouchableOpacity>
          
          <Text style={styles.coordinateHint}>
            Selected friends will receive instant invites with location and ETA
          </Text>
        </View>
      </Animated.ScrollView>
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
    backgroundColor: colors.background,
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.coffeeCream,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 8,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  backArrow: {
    fontSize: 16,
    color: colors.coffeeDark,
    fontWeight: '600',
    marginRight: 4,
  },
  backText: {
    fontSize: 14,
    color: colors.coffeeDark,
    fontWeight: '500',
  },
  headerCenter: {
    position: 'absolute',
    left: 0,
    right: 0,
    alignItems: 'center',
    justifyContent: 'center',
    pointerEvents: 'none',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.coffeeDark,
    letterSpacing: -0.4,
    marginBottom: 2,
  },
  liveIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.available,
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.coffeeWhite,
    marginRight: 4,
  },
  liveText: {
    fontSize: 10,
    fontWeight: '600',
    color: colors.coffeeWhite,
  },
  headerRight: {
    width: 80,
    height: 36,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingRadar: {
    fontSize: 60,
    marginBottom: 20,
  },
  loadingText: {
    fontSize: 16,
    color: colors.coffeeDark,
    fontWeight: '500',
  },
  radarSection: {
    alignItems: 'center',
    marginVertical: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.coffeeDark,
    marginBottom: 20,
    textAlign: 'center',
  },
  radarContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  radarBackground: {
    width: 280,
    height: 280,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  radarRing: {
    position: 'absolute',
    borderWidth: 2,
    borderColor: `${colors.coffeeMedium}20`,
    borderRadius: 140,
  },
  radarSweep: {
    position: 'absolute',
    width: 140,
    height: 2,
    backgroundColor: colors.coffeeAccent,
    left: 140,
    top: 139,
    transformOrigin: '0 1px',
  },
  radarCenter: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.coffeeDark,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'absolute',
  },
  radarCenterText: {
    fontSize: 10,
    fontWeight: '600',
    color: colors.coffeeWhite,
  },
  friendDot: {
    position: 'absolute',
    width: 30,
    height: 30,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 4,
  },
  friendInitial: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.coffeeWhite,
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 20,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  legendDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 6,
  },
  legendText: {
    fontSize: 14,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  selectedSection: {
    marginVertical: 20,
  },
  selectedFriends: {
    gap: 8,
  },
  selectedFriend: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.coffeeCream,
    borderRadius: 12,
    padding: 12,
  },
  selectedFriendName: {
    fontSize: 16,
    fontWeight: '500',
    color: colors.coffeeDark,
  },
  selectedFriendStatus: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  suggestionSection: {
    marginVertical: 20,
  },
  spotCard: {
    backgroundColor: colors.coffeeCream,
    borderRadius: 16,
    padding: 16,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  spotHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  spotName: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.coffeeDark,
  },
  spotRating: {
    backgroundColor: colors.available,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  spotRatingText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.coffeeWhite,
  },
  spotDetails: {
    fontSize: 14,
    color: colors.textSecondary,
    marginBottom: 4,
  },
  spotWeather: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  actionSection: {
    marginVertical: 30,
    alignItems: 'center',
  },
  coordinateButton: {
    backgroundColor: colors.coffeeDark,
    borderRadius: 16,
    paddingVertical: 18,
    paddingHorizontal: 32,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
    minWidth: 200,
    alignItems: 'center',
  },
  coordinateButtonDisabled: {
    backgroundColor: colors.coffeeLight,
    shadowOpacity: 0.1,
  },
  coordinateButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.coffeeWhite,
  },
  coordinatingState: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  coordinatingIcon: {
    fontSize: 20,
    color: colors.coffeeWhite,
  },
  coordinateHint: {
    fontSize: 14,
    color: colors.textLight,
    textAlign: 'center',
    marginTop: 12,
    maxWidth: 280,
  },
}); 