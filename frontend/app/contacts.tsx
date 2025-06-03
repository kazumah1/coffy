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
  TextInput,
  SafeAreaView,
  Animated,
  Easing
} from 'react-native';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import * as Contacts from 'expo-contacts';
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

// Define our app's contact type that matches the backend
interface AppContact {
  id: string;
  name: string;
  phoneNumbers?: { number: string }[];
  emails?: { email: string }[];
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

// Convert expo-contacts Contact to our AppContact type
const convertToAppContact = (contact: Contacts.Contact): AppContact => ({
  id: contact.id || '',
  name: contact.name || 'Unknown',
  phoneNumbers: contact.phoneNumbers?.map(p => ({ number: p.number || '' })).filter(p => p.number) || [],
  emails: contact.emails?.map(e => ({ email: e.email || '' })).filter(e => e.email) || []
});

export default function ContactsScreen() {
  const { user } = useAuth();
  const [contacts, setContacts] = useState<AppContact[]>([]);
  const [filteredContacts, setFilteredContacts] = useState<AppContact[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [savedContactsCount, setSavedContactsCount] = useState(0);
  
  // Animation values
  const fadeAnim = new Animated.Value(0);
  const slideAnim = new Animated.Value(50);

  useEffect(() => {
    loadContacts();
    if (user) {
      checkSavedContacts();
    }
    
    // Entrance animation
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
        easing: Easing.out(Easing.ease),
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 600,
        easing: Easing.out(Easing.ease),
        useNativeDriver: true,
      }),
    ]).start();
  }, [user]);

  useEffect(() => {
    if (searchQuery) {
      const filtered = contacts.filter(contact =>
        contact.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredContacts(filtered);
    } else {
      setFilteredContacts(contacts);
    }
  }, [searchQuery, contacts]);

  const loadContacts = async () => {
    setLoading(true);
    console.log('🔍 Loading contacts...');
    
    try {
      // Request permission to access contacts
      const { status } = await Contacts.requestPermissionsAsync();
      if (status !== 'granted') {
        console.log('❌ Permission to access contacts was denied');
        Alert.alert(
          'Permission Required',
          'Please grant permission to access your contacts to use this feature.',
          [{ text: 'OK' }]
        );
        setLoading(false);
        return;
      }

      // Get all contacts from device
      const { data: deviceContacts } = await Contacts.getContactsAsync({
        fields: [
          Contacts.Fields.Name,
          Contacts.Fields.PhoneNumbers,
          Contacts.Fields.Emails,
        ],
      });

      console.log(`📱 Found ${deviceContacts.length} contacts on device`);

      // Convert to our app's contact type
      const appContacts = deviceContacts.map(convertToAppContact);

      // Sync with backend if user is logged in
      if (user) {
        console.log('📱 Syncing contacts with backend...');
        const response = await fetchWithTimeout(`${BACKEND_URL}/contacts/sync`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: user.id,
            contacts: appContacts
          }),
        });

        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            console.log(`✅ Successfully synced ${appContacts.length} contacts with backend`);
          }
        } else {
          console.log('⚠️ Could not sync with backend, saving contacts locally only');
        }
      }

      // Update state and local storage
      setContacts(appContacts);
      await SecureStore.setItemAsync('userContacts', JSON.stringify(appContacts));
      console.log(`✅ Loaded ${appContacts.length} contacts`);
    } catch (error) {
      console.error('💥 Error loading contacts:', error);
      setContacts([]);
    } finally {
      setLoading(false);
      console.log('🏁 Contacts loading complete');
    }
  };

  const checkSavedContacts = async () => {
    if (!user) return;
    
    try {
      console.log('📱 Checking saved contacts count from backend...');
      const response = await fetchWithTimeout(`${BACKEND_URL}/api/contacts/best-friends/${user.id}`);
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          console.log(`✅ Found ${data.contacts.length} contacts in backend`);
          setSavedContactsCount(data.contacts.length);
        }
      } else {
        console.log('⚠️ Could not check backend contacts count');
      }
    } catch (error) {
      console.error('💥 Error checking saved contacts:', error);
    }
  };

  const goBack = () => {
    router.back();
  };

  const navigateToBestFriends = () => {
    if (contacts.length === 0) {
      Alert.alert(
        'Load Contacts First',
        'Please load your contacts before selecting your coffee crew.',
        [{ text: 'Got It' }]
      );
      return;
    }
    router.push('/best-friends');
  };

  const goToProfileSetup = () => {
    router.push('/profile-setup' as any);
  };

  const refreshContacts = async () => {
    await loadContacts();
    if (contacts.length === 0) {
      Alert.alert(
        'No Contacts Found',
        'Please complete your profile setup to load contacts first.',
        [
          { text: 'Go to Setup', onPress: goToProfileSetup },
          { text: 'Cancel', style: 'cancel' }
        ]
      );
    }
  };

  const renderContact = ({ item, index }: { item: AppContact; index: number }) => {
    const phoneNumber = item.phoneNumbers?.[0]?.number || '';
    const email = item.emails?.[0]?.email || '';

    return (
      <Animated.View 
        style={[
          styles.contactItem,
          {
            opacity: fadeAnim,
            transform: [
              {
                translateY: slideAnim.interpolate({
                  inputRange: [0, 50],
                  outputRange: [0, 50],
                }),
              },
            ],
          },
        ]}
      >
        <View style={styles.contactAvatar}>
          <Text style={styles.contactInitial}>
            {item.name.charAt(0).toUpperCase()}
          </Text>
        </View>
        
        <View style={styles.contactInfo}>
          <Text style={styles.contactName}>{item.name}</Text>
          <Text style={styles.contactDetail}>
            {phoneNumber || email || 'No contact info'}
          </Text>
        </View>
      </Animated.View>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" backgroundColor={colors.background} />
        
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={goBack}>
            <Text style={styles.backButtonText}>✕</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Contacts</Text>
        </View>

        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.coffeeMedium} />
          <Text style={styles.loadingText}>Loading contacts...</Text>
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
        <Text style={styles.headerTitle}>Contacts</Text>
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
        {contacts.length === 0 ? (
          // Empty State
          <View style={styles.emptyContainer}>
            <View style={styles.emptyIcon}>
              <Text style={styles.emptyIconText}>📱</Text>
            </View>
            <Text style={styles.emptyTitle}>Contacts Not Loaded</Text>
            <Text style={styles.emptySubtitle}>
              Complete your profile setup to load contacts and start building your coffee crew
            </Text>
            
            <TouchableOpacity 
              style={styles.loadButton} 
              onPress={goToProfileSetup}
            >
              <Text style={styles.loadButtonText}>Complete Profile Setup</Text>
            </TouchableOpacity>

            {/* Temporary Debug Button */}
            <TouchableOpacity 
              style={[styles.loadButton, { backgroundColor: colors.coffeeAccent, marginTop: 16 }]} 
              onPress={loadContacts}
            >
              <Text style={styles.loadButtonText}>🔍 Debug: Reload Contacts</Text>
            </TouchableOpacity>
          </View>
        ) : (
          // Contacts List
          <>
            {/* Search Bar */}
            <View style={styles.searchContainer}>
              <View style={styles.searchBar}>
                <Text style={styles.searchIcon}>🔍</Text>
                <TextInput
                  style={styles.searchInput}
                  placeholder="Search contacts..."
                  placeholderTextColor={colors.textLight}
                  value={searchQuery}
                  onChangeText={setSearchQuery}
                />
              </View>
            </View>

            {/* Stats Bar */}
            <View style={styles.statsContainer}>
              <Text style={styles.statsText}>
                {filteredContacts.length} contact{filteredContacts.length !== 1 ? 's' : ''}
              </Text>
              <TouchableOpacity style={styles.bestFriendsButton} onPress={navigateToBestFriends}>
                <Text style={styles.bestFriendsText}>Select Coffee Crew</Text>
                <Text style={styles.bestFriendsArrow}>→</Text>
              </TouchableOpacity>
            </View>

            {/* Contacts List */}
            <FlatList
              data={filteredContacts}
              renderItem={renderContact}
              keyExtractor={(item) => item.id}
              showsVerticalScrollIndicator={false}
              contentContainerStyle={styles.listContainer}
            />
          </>
        )}
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
  permissionContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
  },
  permissionIcon: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: colors.coffeeCream,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 6,
  },
  permissionImage: {
    width: 70,
    height: 70,
  },
  permissionTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.coffeeDark,
    textAlign: 'center',
    marginBottom: 12,
    letterSpacing: -0.5,
  },
  permissionSubtitle: {
    fontSize: 16,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
    maxWidth: 280,
  },
  permissionButton: {
    backgroundColor: colors.coffeeDark,
    borderRadius: 16,
    paddingVertical: 16,
    paddingHorizontal: 32,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
  },
  permissionButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.coffeeWhite,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
  },
  emptyIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.coffeeCream,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  emptyIconText: {
    fontSize: 40,
  },
  emptyTitle: {
    fontSize: 22,
    fontWeight: '600',
    color: colors.coffeeDark,
    textAlign: 'center',
    marginBottom: 12,
    letterSpacing: -0.5,
  },
  emptySubtitle: {
    fontSize: 16,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
    maxWidth: 280,
  },
  loadButton: {
    backgroundColor: colors.coffeeDark,
    borderRadius: 16,
    paddingVertical: 16,
    paddingHorizontal: 32,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
    minWidth: 160,
    alignItems: 'center',
  },
  loadButtonDisabled: {
    backgroundColor: colors.coffeeLight,
    shadowOpacity: 0.1,
  },
  loadButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.coffeeWhite,
  },
  searchContainer: {
    paddingVertical: 20,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.coffeeCream,
    borderRadius: 16,
    paddingHorizontal: 16,
    paddingVertical: 12,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  searchIcon: {
    fontSize: 18,
    marginRight: 12,
    opacity: 0.6,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: colors.textPrimary,
    lineHeight: 22,
  },
  statsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  statsText: {
    fontSize: 14,
    color: colors.textLight,
    fontWeight: '500',
  },
  bestFriendsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.coffeeDark,
    borderRadius: 12,
    paddingVertical: 8,
    paddingHorizontal: 12,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 3,
  },
  bestFriendsText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.coffeeWhite,
    marginRight: 4,
  },
  bestFriendsArrow: {
    fontSize: 16,
    color: colors.coffeeWhite,
    fontWeight: '600',
  },
  listContainer: {
    paddingBottom: 20,
  },
  contactItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.background,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: `${colors.coffeeMedium}15`,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  contactAvatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: colors.coffeeMedium,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  contactInitial: {
    fontSize: 20,
    fontWeight: '600',
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
  contactDetail: {
    fontSize: 14,
    color: colors.textLight,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: colors.coffeeDark,
    fontWeight: '500',
    marginTop: 20,
  },
}); 