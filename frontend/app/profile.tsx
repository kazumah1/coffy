import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  TouchableOpacity, 
  StyleSheet, 
  StatusBar,
  ScrollView,
  TextInput,
  Alert,
  SafeAreaView,
  ActivityIndicator
} from 'react-native';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useAuth } from '@/contexts/AuthContext';
import * as SecureStore from 'expo-secure-store';
import * as Contacts from 'expo-contacts';
// Note: expo-image-picker requires development build rebuild
// For now, using a simpler approach

// Define our app's contact type that matches the backend
interface AppContact {
  id: string;
  name: string;
  phoneNumbers?: { number: string }[];
  emails?: { email: string }[];
}

// Convert expo-contacts Contact to our AppContact type
const convertToAppContact = (contact: Contacts.Contact): AppContact => ({
  id: contact.id || '',
  name: contact.name || 'Unknown',
  phoneNumbers: contact.phoneNumbers?.map(p => ({ number: p.number || '' })).filter(p => p.number) || [],
  emails: contact.emails?.map(e => ({ email: e.email || '' })).filter(e => e.email) || []
});

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

const BACKEND_URL = "https://www.coffy.app";
const REQUEST_TIMEOUT = 30000; // 30 seconds timeout

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

export default function ProfileScreen() {
  const { user, signOut } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [profileImage, setProfileImage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [userStatus, setUserStatus] = useState<'available' | 'maybe' | 'busy'>('available');
  const [syncingContacts, setSyncingContacts] = useState(false);

  // Load existing profile data when component mounts
  useEffect(() => {
    loadProfileData();
    loadAvailabilityStatus();
  }, []);

  const loadProfileData = async () => {
    if (!user?.id) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/users/profile/${user.id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 404) {
        // Backend endpoint doesn't exist yet - try to load from local storage
        console.log('Backend endpoint not available, loading from local storage');
        const localProfile = await SecureStore.getItemAsync('userProfile');
        if (localProfile) {
          const profileData = JSON.parse(localProfile);
          if (profileData.name) setName(profileData.name);
          if (profileData.phone_number) setPhoneNumber(profileData.phone_number);
        }
        return;
      }

      if (response.ok) {
        const profileData = await response.json();
        if (profileData.name) setName(profileData.name);
        if (profileData.phone_number) setPhoneNumber(profileData.phone_number);
        if (profileData.profile_image_url) setProfileImage(profileData.profile_image_url);
      }
    } catch (error) {
      console.error('Error loading profile:', error);
      // Fallback to local storage
      try {
        const localProfile = await SecureStore.getItemAsync('userProfile');
        if (localProfile) {
          const profileData = JSON.parse(localProfile);
          if (profileData.name) setName(profileData.name);
          if (profileData.phone_number) setPhoneNumber(profileData.phone_number);
        }
      } catch (localError) {
        console.error('Error loading local profile:', localError);
      }
    } finally {
      setLoadingProfile(false);
    }
  };

  const loadAvailabilityStatus = async () => {
    try {
      const savedStatus = await SecureStore.getItemAsync('userAvailabilityStatus');
      if (savedStatus) {
        setUserStatus(savedStatus as 'available' | 'maybe' | 'busy');
      }
    } catch (error) {
      console.error('Error loading availability status:', error);
    }
  };

  const toggleAvailabilityStatus = async () => {
    const statuses: ('available' | 'maybe' | 'busy')[] = ['available', 'maybe', 'busy'];
    const currentIndex = statuses.indexOf(userStatus);
    const nextStatus = statuses[(currentIndex + 1) % statuses.length];
    setUserStatus(nextStatus);
    
    // Save status locally
    try {
      await SecureStore.setItemAsync('userAvailabilityStatus', nextStatus);
    } catch (error) {
      console.error('Error saving availability status:', error);
    }
    
    // Here you could sync with backend API
    // syncAvailabilityWithBackend(nextStatus);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return '#4CAF50';
      case 'maybe': return '#FF9800';
      case 'busy': return '#F44336';
      default: return colors.coffeeMedium;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'available': return '☕ Available for Coffy';
      case 'maybe': return '🤔 Maybe Available';
      case 'busy': return '⏰ Busy Right Now';
      default: return 'Set Status';
    }
  };

  const goBack = () => {
    router.back();
  };

  const pickImage = async () => {
    // Alternative approach - let users know about profile picture options
    Alert.alert(
      'Profile Picture Options', 
      'To change your profile picture:\n\n• Use a web browser to upload photos\n• Or we can add this feature in the next app update\n\nFor now, you can customize your display name!',
      [
        { text: 'OK', style: 'default' },
        { 
          text: 'Use Default Images', 
          onPress: () => {
            // Cycle through some default profile images
            const defaultImages = [
              require('@/assets/images/coffee-character.png'),
              // Could add more default options here
            ];
            setProfileImage(null); // Keep using the default character
            Alert.alert('Updated!', 'Using default coffee character as your profile picture.');
          }
        }
      ]
    );
  };

  const saveProfile = async () => {
    if (!name.trim()) {
      Alert.alert('Required Field', 'Please enter your name.');
      return;
    }

    if (!phoneNumber.trim()) {
      Alert.alert('Required Field', 'Please enter your phone number.');
      return;
    }

    // Basic phone number validation
    const phoneRegex = /^\+?[\d\s\-\(\)]{10,}$/;
    if (!phoneRegex.test(phoneNumber.trim())) {
      Alert.alert('Invalid Phone', 'Please enter a valid phone number.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/auth/users/update-profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user?.id,
          name: name.trim(),
          phone_number: phoneNumber.trim(),
          email: user?.email
        }),
      });

      if (response.status === 404) {
        // Backend endpoint doesn't exist yet - save locally
        console.log('Backend endpoint not available, saving locally');
        await SecureStore.setItemAsync('userProfile', JSON.stringify({
          name: name.trim(),
          phone_number: phoneNumber.trim(),
          user_id: user?.id,
          profile_image_url: profileImage
        }));
        
        Alert.alert('Profile Saved!', 'Your profile has been saved locally. Will sync when backend is available.', [
          { text: 'OK', onPress: () => router.back() }
        ]);
        return;
      }

      if (response.ok) {
        Alert.alert('Success', 'Profile updated successfully!', [
          { text: 'OK', onPress: () => router.back() }
        ]);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update profile');
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      
      // Fallback: save locally
      try {
        await SecureStore.setItemAsync('userProfile', JSON.stringify({
          name: name.trim(),
          phone_number: phoneNumber.trim(),
          user_id: user?.id,
          profile_image_url: profileImage
        }));
        
        Alert.alert('Saved Locally', 'Profile saved on device. Will sync when connection is available.', [
          { text: 'OK', onPress: () => router.back() }
        ]);
      } catch (localError) {
        Alert.alert('Error', 'Failed to save profile. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const syncContacts = async () => {
    setSyncingContacts(true);
    console.log('🔍 Starting contacts sync...');
    
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
        return;
      }

      // Get all contacts from device with pagination
      let allContacts: Contacts.Contact[] = [];
      let hasNextPage = true;
      let pageOffset = 0;
      const pageSize = 50; // Match the page size from contacts.tsx

      while (hasNextPage) {
        const { data: deviceContacts, hasNextPage: nextPage } = await Contacts.getContactsAsync({
          fields: [
            Contacts.Fields.Name,
            Contacts.Fields.PhoneNumbers,
            Contacts.Fields.Emails,
          ],
          pageSize,
          pageOffset,
        });

        allContacts = [...allContacts, ...deviceContacts];
        hasNextPage = nextPage;
        pageOffset += pageSize;
        
        console.log(`📱 Retrieved ${deviceContacts.length} contacts (page ${pageOffset/pageSize})`);
      }

      console.log(`📱 Found total of ${allContacts.length} contacts on device`);

      // Convert to our app's contact type
      const appContacts = allContacts.map(convertToAppContact);

      // Sync with backend if user is logged in
      if (user) {
        console.log('📱 Syncing contacts with backend...');
        try {
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
              Alert.alert('Success', `Successfully synced ${appContacts.length} contacts!`);
            }
          } else {
            const errorData = await response.json().catch(() => null);
            console.error('⚠️ Backend sync failed:', {
              status: response.status,
              statusText: response.statusText,
              error: errorData
            });
            throw new Error('Failed to sync contacts with backend');
          }
        } catch (error) {
          console.error('💥 Error during backend sync:', error);
          throw error;
        }
      }

      // Update local storage
      await SecureStore.setItemAsync('userContacts', JSON.stringify(appContacts));
      console.log(`✅ Loaded ${appContacts.length} contacts`);
    } catch (error) {
      console.error('💥 Error syncing contacts:', error);
      Alert.alert('Error', 'Failed to sync contacts. Please try again.');
    } finally {
      setSyncingContacts(false);
      console.log('🏁 Contacts sync complete');
    }
  };

  if (loadingProfile) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" backgroundColor={colors.background} />
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading profile...</Text>
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
        <Text style={styles.headerTitle}>Profile Settings</Text>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Profile Picture Section */}
        <View style={styles.profileSection}>
          <Text style={styles.sectionTitle}>Profile Picture</Text>
          
          <TouchableOpacity style={styles.profileImageContainer} onPress={pickImage}>
            {profileImage ? (
              <Image 
                source={{ uri: profileImage }}
                style={styles.profileImage}
                contentFit="cover"
              />
            ) : (
              <View style={styles.defaultProfileImage}>
                <Image 
                  source={require('@/assets/images/coffee-character.png')} 
                  style={styles.defaultImage}
                  contentFit="contain"
                />
              </View>
            )}
            <View style={styles.editOverlay}>
              <Text style={styles.editText}>📷</Text>
            </View>
          </TouchableOpacity>
          
          <Text style={styles.profileHint}>Tap to change your profile picture</Text>
        </View>

        {/* Name Section */}
        <View style={styles.nameSection}>
          <Text style={styles.sectionTitle}>Display Name</Text>
          
          <View style={styles.inputWrapper}>
            <TextInput
              style={styles.nameInput}
              value={name}
              onChangeText={setName}
              placeholder="Enter your name"
              placeholderTextColor={colors.textLight}
              autoCapitalize="words"
              maxLength={50}
            />
          </View>
          
          <Text style={styles.inputHint}>
            This is how your name will appear to friends when Joe sends messages on your behalf.
          </Text>
        </View>

        {/* Phone Number Section */}
        <View style={styles.phoneSection}>
          <Text style={styles.sectionTitle}>Phone Number</Text>
          
          <View style={styles.inputWrapper}>
            <TextInput
              style={styles.phoneInput}
              value={phoneNumber}
              onChangeText={setPhoneNumber}
              placeholder="+1 (555) 123-4567"
              placeholderTextColor={colors.textLight}
              keyboardType="phone-pad"
              maxLength={20}
            />
          </View>
          
          <Text style={styles.inputHint}>
            Joe will use this number to coordinate coffee meetups with your friends.
          </Text>
        </View>

        {/* Account Info */}
        <View style={styles.accountSection}>
          <Text style={styles.sectionTitle}>Account Information</Text>
          
          <View style={styles.infoCard}>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Email</Text>
              <Text style={styles.infoValue}>{user?.email}</Text>
            </View>
          </View>
        </View>

        {/* Availability Status */}
        {/* <View style={styles.availabilitySection}>
          <Text style={styles.sectionTitle}>Coffy Availability</Text>
          
          <TouchableOpacity 
            style={[styles.statusToggle, { borderColor: getStatusColor(userStatus) }]}
            onPress={toggleAvailabilityStatus}
            activeOpacity={0.8}
          >
            <View style={[styles.statusDot, { backgroundColor: getStatusColor(userStatus) }]} />
            <View style={styles.statusTextContainer}>
              <Text style={styles.statusMainText}>{getStatusText(userStatus)}</Text>
              <Text style={styles.statusSubText}>Tap to change</Text>
            </View>
          </TouchableOpacity>
          
          <Text style={styles.statusHint}>
            Your availability status helps friends see when you're free for spontaneous Coffy meetups through Coffy Radar.
          </Text>
        </View> */}

        {/* Action Buttons */}
        <View style={styles.actionsSection}>
          <TouchableOpacity 
            style={[styles.saveButton, isLoading && styles.saveButtonDisabled]} 
            onPress={saveProfile}
            disabled={isLoading}
          >
            <Text style={styles.saveButtonText}>
              {isLoading ? 'Saving...' : 'Save Changes'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.syncButton} 
            onPress={syncContacts}
            disabled={syncingContacts}
          >
            {syncingContacts ? (
              <ActivityIndicator color={colors.coffeeDark} />
            ) : (
              <Text style={styles.syncButtonText}>Sync Contacts</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity style={styles.signOutButton} onPress={signOut}>
            <Text style={styles.signOutText}>Sign Out</Text>
          </TouchableOpacity>
        </View>
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
  profileSection: {
    alignItems: 'center',
    paddingVertical: 30,
    borderBottomWidth: 1,
    borderBottomColor: `${colors.coffeeMedium}10`,
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.coffeeDark,
    marginBottom: 20,
    alignSelf: 'flex-start',
    width: '100%',
  },
  profileImageContainer: {
    position: 'relative',
    marginBottom: 12,
  },
  profileImage: {
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 4,
    borderColor: colors.coffeeCream,
  },
  defaultProfileImage: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: colors.coffeeCream,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 4,
    borderColor: colors.coffeeLight,
  },
  defaultImage: {
    width: 80,
    height: 80,
    opacity: 0.6,
  },
  editOverlay: {
    position: 'absolute',
    bottom: 5,
    right: 5,
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.coffeeMedium,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 4,
  },
  editText: {
    fontSize: 18,
    color: colors.coffeeWhite,
  },
  profileHint: {
    fontSize: 14,
    color: colors.textLight,
    textAlign: 'center',
  },
  nameSection: {
    marginBottom: 30,
  },
  inputWrapper: {
    backgroundColor: colors.background,
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: `${colors.coffeeMedium}20`,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
    marginBottom: 8,
  },
  nameInput: {
    paddingHorizontal: 16,
    paddingVertical: 16,
    fontSize: 16,
    color: colors.textPrimary,
    lineHeight: 22,
  },
  inputHint: {
    fontSize: 14,
    color: colors.textLight,
    lineHeight: 20,
  },
  phoneSection: {
    marginBottom: 30,
  },
  phoneInput: {
    paddingHorizontal: 16,
    paddingVertical: 16,
    fontSize: 16,
    color: colors.textPrimary,
    lineHeight: 22,
  },
  accountSection: {
    marginBottom: 40,
  },
  infoCard: {
    backgroundColor: colors.coffeeCream,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: `${colors.coffeeMedium}15`,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  infoLabel: {
    fontSize: 16,
    fontWeight: '500',
    color: colors.coffeeDark,
  },
  infoValue: {
    fontSize: 16,
    color: colors.textSecondary,
  },
  availabilitySection: {
    marginBottom: 40,
  },
  statusToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.coffeeCream,
    borderRadius: 16,
    padding: 16,
    borderWidth: 2,
    borderColor: colors.coffeeMedium,
  },
  statusDot: {
    width: 20,
    height: 20,
    borderRadius: 10,
    marginRight: 12,
  },
  statusTextContainer: {
    flex: 1,
  },
  statusMainText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.coffeeDark,
    marginBottom: 4,
  },
  statusSubText: {
    fontSize: 14,
    color: colors.textLight,
  },
  statusHint: {
    fontSize: 14,
    color: colors.textLight,
    textAlign: 'center',
  },
  actionsSection: {
    gap: 16,
    marginBottom: 40,
  },
  saveButton: {
    backgroundColor: colors.coffeeDark,
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: 'center',
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  saveButtonDisabled: {
    backgroundColor: colors.coffeeLight,
    shadowOpacity: 0.1,
  },
  saveButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.coffeeWhite,
  },
  syncButton: {
    backgroundColor: colors.coffeeCream,
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: colors.coffeeMedium,
    flexDirection: 'row',
    justifyContent: 'center',
  },
  syncButtonText: {
    fontSize: 16,
    fontWeight: '500',
    color: colors.coffeeDark,
  },
  signOutButton: {
    backgroundColor: colors.background,
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: `${colors.coffeeMedium}30`,
  },
  signOutText: {
    fontSize: 16,
    fontWeight: '500',
    color: colors.textSecondary,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.coffeeDark,
  },
}); 