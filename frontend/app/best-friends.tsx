import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  FlatList, 
  TouchableOpacity, 
  StyleSheet, 
  StatusBar,
  Alert,
  ActivityIndicator,
  Animated,
  SafeAreaView,
  Easing
} from 'react-native';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import * as Haptics from 'expo-haptics';
import { useAuth } from '@/contexts/AuthContext';
import * as SecureStore from 'expo-secure-store';

const BACKEND_URL = "https://www.coffy.app";
const REQUEST_TIMEOUT = 3000; // 3 seconds timeout

// Coffee-themed color palette
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

interface Contact {
  id: string;
  name: string;
  phoneNumbers?: { number: string }[];
  emails?: { email: string }[];
}

interface BestFriend extends Contact {
  isBestFriend: boolean;
}

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

export default function BestFriendsScreen() {
  const { user } = useAuth();
  const [contacts, setContacts] = useState<BestFriend[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedCount, setSelectedCount] = useState(0);
  
  // Animation values
  const fadeAnim = new Animated.Value(0);
  const slideAnim = new Animated.Value(50);
  const headerScale = new Animated.Value(0.8);

  useEffect(() => {
    loadContactsAndBestFriends();
    
    // Entrance animations
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
      Animated.spring(headerScale, {
        toValue: 1,
        tension: 100,
        friction: 8,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const loadContactsAndBestFriends = async () => {
    if (!user) return;
    
    try {
      // First try to load contacts from local storage
      const savedContacts = await SecureStore.getItemAsync('userContacts');
      if (savedContacts) {
        const contactsData = JSON.parse(savedContacts);
        const contactsWithBestFriends = contactsData.map((contact: Contact) => ({
          ...contact,
          isBestFriend: false
        }));
        
        // Try to load best friends selection from backend or local storage
        try {
          const response = await fetchWithTimeout(`${BACKEND_URL}/api/contacts/best-friends/${user.id}`);
          
          if (response.status !== 404 && response.ok) {
            const data = await response.json();
            if (data.success && data.contacts) {
              // Mark best friends from backend
              const bestFriendIds = data.contacts.filter((c: BestFriend) => c.isBestFriend).map((c: BestFriend) => c.id);
              contactsWithBestFriends.forEach((contact: BestFriend) => {
                contact.isBestFriend = bestFriendIds.includes(contact.id);
              });
            }
          } else {
            // Fallback to local storage for best friends
            const localBestFriends = await SecureStore.getItemAsync('userBestFriends');
            if (localBestFriends) {
              const bestFriendIds = JSON.parse(localBestFriends);
              contactsWithBestFriends.forEach((contact: BestFriend) => {
                contact.isBestFriend = bestFriendIds.includes(contact.id);
              });
            }
          }
        } catch (error) {
          console.log('Could not load best friends data, using default');
          // Try local storage fallback
          try {
            const localBestFriends = await SecureStore.getItemAsync('userBestFriends');
            if (localBestFriends) {
              const bestFriendIds = JSON.parse(localBestFriends);
              contactsWithBestFriends.forEach((contact: BestFriend) => {
                contact.isBestFriend = bestFriendIds.includes(contact.id);
              });
            }
          } catch (localError) {
            console.log('Could not load from local storage either');
          }
        }
        
        setContacts(contactsWithBestFriends);
        setSelectedCount(contactsWithBestFriends.filter((c: BestFriend) => c.isBestFriend).length);
      } else {
        // No contacts found - redirect to profile setup
        Alert.alert(
          'Complete Profile Setup',
          'Please complete your profile setup to load contacts first.',
          [
            {
              text: 'Go to Profile Setup',
              onPress: () => router.push('/profile-setup')
            }
          ]
        );
        return;
      }
    } catch (error) {
      console.error('Error loading contacts and best friends:', error);
      Alert.alert(
        'Error Loading Contacts',
        'Please complete your profile setup to load contacts first.',
        [
          {
            text: 'Go to Profile Setup',
            onPress: () => router.push('/profile-setup')
          }
        ]
      );
    } finally {
      setLoading(false);
    }
  };

  const toggleBestFriend = async (contactId: string) => {
    // Haptic feedback for better UX
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    
    setContacts(prevContacts => {
      const updated = prevContacts.map(contact => {
        if (contact.id === contactId) {
          return { ...contact, isBestFriend: !contact.isBestFriend };
        }
        return contact;
      });
      
      setSelectedCount(updated.filter(c => c.isBestFriend).length);
      return updated;
    });
  };

  const saveBestFriends = async () => {
    if (!user) return;
    
    if (selectedCount === 0) {
      Alert.alert(
        'Select Your Coffee Crew',
        'Please select at least one friend to add to your coffee crew.',
        [{ text: 'Got It' }]
      );
      return;
    }
    
    setSaving(true);
    try {
      const bestFriends = contacts.filter(contact => contact.isBestFriend);
      const bestFriendIds = bestFriends.map(contact => contact.id);
      
      // Save locally first
      await SecureStore.setItemAsync('userBestFriends', JSON.stringify(bestFriendIds));
      
      const response = await fetchWithTimeout(`${BACKEND_URL}/api/contacts/best-friends/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user.id,
          best_friends: bestFriends
        }),
      });

      if (response.status === 404) {
        // Backend not available - saved locally already
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        Alert.alert(
          'Coffee Crew Saved! ☕', 
          `Selected ${selectedCount} friend${selectedCount !== 1 ? 's' : ''} for your coffee crew! Saved locally and will sync when server is available.`,
          [
            {
              text: 'Perfect',
              onPress: () => router.back()
            }
          ]
        );
        return;
      }

      const data = await response.json();
      
      if (data.success) {
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        Alert.alert(
          'Coffee Crew Ready! ☕', 
          `Saved ${selectedCount} friend${selectedCount !== 1 ? 's' : ''} to your coffee crew! Joe can now help coordinate meetups.`,
          [
            {
              text: 'Perfect',
              onPress: () => router.back()
            }
          ]
        );
      } else {
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
        Alert.alert('Oops!', 'Failed to save your coffee crew. Please try again.');
      }
    } catch (error) {
      console.error('Error saving best friends:', error);
      // Already saved locally above
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert(
        'Saved Locally ☕', 
        `Your coffee crew of ${selectedCount} friend${selectedCount !== 1 ? 's' : ''} has been saved locally and will sync when connection is available.`,
        [
          {
            text: 'Got It',
            onPress: () => router.back()
          }
        ]
      );
    } finally {
      setSaving(false);
    }
  };

  const clearAllSelections = () => {
    Alert.alert(
      'Clear All Selections?',
      'This will remove all friends from your coffee crew selection.',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Clear All',
          style: 'destructive',
          onPress: () => {
            setContacts(prevContacts => 
              prevContacts.map(contact => ({ ...contact, isBestFriend: false }))
            );
            setSelectedCount(0);
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          },
        },
      ]
    );
  };

  const goBack = () => {
    router.back();
  };

  const ContactItem = ({ item, index }: { item: BestFriend; index: number }) => {
    const [scaleValue] = useState(new Animated.Value(1));
    const phoneNumber = item.phoneNumbers?.[0]?.number || '';
    const email = item.emails?.[0]?.email || '';

    const handlePress = () => {
      // Scale animation for visual feedback
      Animated.sequence([
        Animated.timing(scaleValue, {
          toValue: 0.95,
          duration: 100,
          useNativeDriver: true,
        }),
        Animated.timing(scaleValue, {
          toValue: 1,
          duration: 100,
          useNativeDriver: true,
        }),
      ]).start();

      toggleBestFriend(item.id);
    };

    return (
      <Animated.View 
        style={{
          opacity: fadeAnim,
          transform: [
            { scale: scaleValue },
            {
              translateY: slideAnim.interpolate({
                inputRange: [0, 50],
                outputRange: [0, 50],
              }),
            },
          ],
        }}
      >
        <TouchableOpacity 
          style={[
            styles.contactItem,
            item.isBestFriend && styles.selectedContactItem
          ]}
          onPress={handlePress}
          activeOpacity={0.7}
        >
          <View style={[
            styles.contactAvatar,
            item.isBestFriend && styles.selectedAvatar
          ]}>
            <Text style={[
              styles.contactInitial,
              item.isBestFriend && styles.selectedInitial
            ]}>
              {item.name.charAt(0).toUpperCase()}
            </Text>
          </View>
          
          <View style={styles.contactInfo}>
            <Text style={[
              styles.contactName,
              item.isBestFriend && styles.selectedContactName
            ]}>
              {item.name}
            </Text>
            <Text style={styles.contactDetail}>
              {phoneNumber || email || 'No contact info'}
            </Text>
          </View>
          
          <View style={[
            styles.selectionIndicator,
            item.isBestFriend && styles.selectedIndicator
          ]}>
            {item.isBestFriend && (
              <Text style={styles.selectionCheckmark}>✓</Text>
            )}
          </View>
        </TouchableOpacity>
      </Animated.View>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" backgroundColor={colors.background} />
        
        <View style={styles.loadingContainer}>
          <View style={styles.loadingIcon}>
            <Image 
              source={require('@/assets/images/coffee-character.png')} 
              style={styles.loadingImage}
              contentFit="contain"
            />
          </View>
          <Text style={styles.loadingTitle}>Loading Coffee Crew...</Text>
          <ActivityIndicator size="large" color={colors.coffeeMedium} style={{ marginTop: 16 }} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.background} />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={goBack}>
          <Text style={styles.backButtonText}>✕</Text>
        </TouchableOpacity>
        <Animated.Text style={[styles.headerTitle, { transform: [{ scale: headerScale }] }]}>
          Coffee Crew
        </Animated.Text>
      </View>

      <Animated.View 
        style={[
          styles.content,
          {
            opacity: fadeAnim,
            transform: [{ translateY: slideAnim }],
          },
        ]}
      >
        {/* Selection Summary */}
        <View style={styles.summaryContainer}>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>
              {selectedCount} Selected
            </Text>
            <Text style={styles.summarySubtitle}>
              Choose friends for your coffee crew
            </Text>
          </View>
          
          {selectedCount > 0 && (
            <TouchableOpacity style={styles.clearButton} onPress={clearAllSelections}>
              <Text style={styles.clearButtonText}>Clear All</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Contacts List */}
        <FlatList
          data={contacts}
          renderItem={({ item, index }) => <ContactItem item={item} index={index} />}
          keyExtractor={(item) => item.id}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.listContainer}
        />

        {/* Save Button */}
        <View style={styles.saveContainer}>
          <TouchableOpacity 
            style={[
              styles.saveButton, 
              saving && styles.saveButtonDisabled,
              selectedCount === 0 && styles.saveButtonInactive
            ]} 
            onPress={saveBestFriends}
            disabled={saving || selectedCount === 0}
          >
            {saving ? (
              <ActivityIndicator size="small" color={colors.coffeeWhite} />
            ) : (
              <Text style={styles.saveButtonText}>
                Save Coffee Crew ({selectedCount})
              </Text>
            )}
          </TouchableOpacity>
        </View>
      </Animated.View>
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
    justifyContent: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: `${colors.coffeeMedium}10`,
    position: 'relative',
  },
  backButton: {
    position: 'absolute',
    left: 20,
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
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.coffeeDark,
    letterSpacing: -0.4,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
  },
  loadingIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.coffeeCream,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  loadingImage: {
    width: 50,
    height: 50,
  },
  loadingTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.coffeeDark,
    textAlign: 'center',
  },
  summaryContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 20,
  },
  summaryCard: {
    flex: 1,
    backgroundColor: colors.coffeeCream,
    borderRadius: 16,
    padding: 16,
    marginRight: 12,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.coffeeDark,
    marginBottom: 4,
  },
  summarySubtitle: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  clearButton: {
    backgroundColor: colors.textLight,
    borderRadius: 12,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  clearButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.coffeeWhite,
  },
  listContainer: {
    paddingBottom: 100,
  },
  contactItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.background,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: `${colors.coffeeMedium}15`,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  selectedContactItem: {
    backgroundColor: colors.coffeeCream,
    borderColor: colors.coffeeMedium,
    shadowOpacity: 0.15,
  },
  contactAvatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: colors.coffeeLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  selectedAvatar: {
    backgroundColor: colors.coffeeDark,
  },
  contactInitial: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.coffeeDark,
  },
  selectedInitial: {
    color: colors.coffeeWhite,
  },
  contactInfo: {
    flex: 1,
  },
  contactName: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.coffeeDark,
    marginBottom: 4,
  },
  selectedContactName: {
    color: colors.coffeeDark,
  },
  contactDetail: {
    fontSize: 14,
    color: colors.textLight,
  },
  selectionIndicator: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: colors.coffeeLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  selectedIndicator: {
    backgroundColor: colors.coffeeDark,
    borderColor: colors.coffeeDark,
  },
  selectionCheckmark: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.coffeeWhite,
  },
  saveContainer: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
  },
  saveButton: {
    backgroundColor: colors.coffeeDark,
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: 'center',
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
  },
  saveButtonDisabled: {
    backgroundColor: colors.coffeeLight,
    shadowOpacity: 0.1,
  },
  saveButtonInactive: {
    backgroundColor: colors.coffeeLight,
    shadowOpacity: 0.1,
  },
  saveButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.coffeeWhite,
  },
}); 