import React, { useState } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  StyleSheet, 
  StatusBar,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  Alert,
  ActivityIndicator,
  Animated,
  Easing
} from 'react-native';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useAuth } from '@/contexts/AuthContext';
import * as SecureStore from 'expo-secure-store';
import * as Contacts from 'expo-contacts';

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

const BACKEND_URL = "http://localhost:8000";
const REQUEST_TIMEOUT = 3000; // 3 seconds timeout

interface Contact {
  id: string;
  name: string;
  phoneNumbers?: { number: string }[];
  emails?: { email: string }[];
}

type SetupStep = 'profile' | 'contacts' | 'complete';

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

export default function ProfileSetupScreen() {
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState<SetupStep>('profile');
  const [name, setName] = useState(user?.name || '');
  const [rawPhoneNumber, setRawPhoneNumber] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [contactsLoading, setContactsLoading] = useState(false);
  const [hasContactsPermission, setHasContactsPermission] = useState(false);
  
  // Animation values
  const fadeAnim = new Animated.Value(1);
  const slideAnim = new Animated.Value(0);

  const animateStepTransition = () => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 200,
        easing: Easing.out(Easing.ease),
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: -50,
        duration: 200,
        easing: Easing.out(Easing.ease),
        useNativeDriver: true,
      }),
    ]).start(() => {
      // Reset position and fade back in
      slideAnim.setValue(50);
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 300,
          easing: Easing.out(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(slideAnim, {
          toValue: 0,
          duration: 300,
          easing: Easing.out(Easing.ease),
          useNativeDriver: true,
        }),
      ]).start();
    });
  };

  const handleProfileComplete = async () => {
    if (!name.trim()) {
      Alert.alert('Required Field', 'Please enter your name to continue.');
      return;
    }

    if (!rawPhoneNumber.trim()) {
      Alert.alert('Required Field', 'Please enter your phone number so Joe can coordinate with your friends.');
      return;
    }

    if (rawPhoneNumber.length !== 10) {
      Alert.alert('Invalid Phone', 'Please enter a valid 10-digit US phone number.');
      return;
    }

    animateStepTransition();
    setTimeout(() => {
      setCurrentStep('contacts');
    }, 200);
  };

  const checkContactsPermission = async () => {
    const { status } = await Contacts.getPermissionsAsync();
    setHasContactsPermission(status === 'granted');
    return status === 'granted';
  };

  const requestContactsPermission = async () => {
    const { status } = await Contacts.requestPermissionsAsync();
    setHasContactsPermission(status === 'granted');
    if (status === 'granted') {
      await loadContacts();
    } else {
      Alert.alert(
        'Contacts Required',
        'Joe needs access to your contacts to help coordinate coffee meetups. Please allow access to continue.',
        [
          { text: 'Try Again', onPress: requestContactsPermission },
          { text: 'Cancel', style: 'cancel' }
        ]
      );
    }
  };

  const loadContacts = async () => {
    setContactsLoading(true);
    console.log('📱 Profile Setup: Starting contacts load...');
    try {
      // Always get contacts from device
      const { status } = await Contacts.getPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Required', 'Please grant permission to access your contacts.');
        setContactsLoading(false);
        return;
      }
      const { data } = await Contacts.getContactsAsync({
        fields: [Contacts.Fields.Name, Contacts.Fields.PhoneNumbers, Contacts.Fields.Emails],
        sort: Contacts.SortTypes.FirstName,
      });
      const formattedContacts = data
        .filter(contact => contact.name && (contact.phoneNumbers || contact.emails))
        .map(contact => ({
          id: contact.id || Math.random().toString(),
          name: contact.name || 'Unknown',
          phoneNumbers: contact.phoneNumbers?.filter(phone => phone.number).map(phone => ({ number: phone.number! })) || [],
          emails: contact.emails?.filter(email => email.email).map(email => ({ email: email.email! })) || []
        }));
      setContacts(formattedContacts);
      await SecureStore.setItemAsync('userContacts', JSON.stringify(formattedContacts));
      console.log('✅ Loaded contacts from device');
      // Sync with backend (using the sync endpoint)
      if (user) {
        await syncContactsWithBackend(formattedContacts);
      }
      Alert.alert(
        'Contacts Loaded! ☕',
        `Successfully loaded ${formattedContacts.length} contacts. Joe can now help coordinate meetups!`,
        [{ text: 'Continue', onPress: proceedToComplete }]
      );
    } catch (error) {
      console.error('💥 Profile Setup: Error loading contacts:', error);
      Alert.alert('Error', 'Couldn\'t load contacts. Please try again.');
    } finally {
      setContactsLoading(false);
    }
  };

  const syncContactsWithBackend = async (contactsList: Contact[]) => {
    try {
      const response = await fetchWithTimeout(`${BACKEND_URL}/contacts/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user?.id,
          contacts: contactsList
        }),
      });

      if (response.status === 404) {
        console.log('Backend endpoint not available yet - contacts saved locally');
        return;
      }

      if (response.ok) {
        console.log('Contacts synced successfully with backend');
      }
    } catch (error) {
      console.log('Could not sync with backend, saved locally');
    }
  };

  const proceedToComplete = () => {
    animateStepTransition();
    setTimeout(() => {
      setCurrentStep('complete');
    }, 200);
  };

  const completeSetup = async () => {
    setIsLoading(true);

    try {
      // Try to save profile to backend
      console.log("Saving profile to backend", user?.id, name.trim(), user?.email, '+1' + rawPhoneNumber)
      const response = await fetchWithTimeout(`${BACKEND_URL}/auth/users/update-profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user?.id,
          name: name.trim(),
          email: user?.email,
          phone_number: '+1' + rawPhoneNumber,
          contacts_loaded: true
        }),
      });

      // Check if the endpoint exists
      if (response.status === 404) {
        console.log('Backend endpoint not implemented yet, saving profile locally');
      } else if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to setup profile');
      }

      // Save profile data locally
      if (user) {
        const updatedUser = { 
          ...user, 
          name: name.trim(),
          needsProfileSetup: false,
          contactsLoaded: true
        };
        await SecureStore.setItemAsync('user', JSON.stringify(updatedUser));
        await SecureStore.setItemAsync('userProfile', JSON.stringify({
          name: name.trim(),
          phone_number: '+1' + rawPhoneNumber,
          user_id: user.id,
          contacts_loaded: true
        }));
      }
      
      // Navigate to main app
      router.replace('/(tabs)');
    } catch (error) {
      console.error('Error setting up profile:', error);
      
      // Fallback: save locally
      if (user) {
        const updatedUser = { 
          ...user, 
          name: name.trim(),
          needsProfileSetup: false,
          contactsLoaded: true
        };
        await SecureStore.setItemAsync('user', JSON.stringify(updatedUser));
        await SecureStore.setItemAsync('userProfile', JSON.stringify({
          name: name.trim(),
          phone_number: '+1' + rawPhoneNumber,
          user_id: user.id,
          contacts_loaded: true
        }));
      }
      
      Alert.alert(
        'Setup Complete', 
        'Profile and contacts saved locally. Will sync when server is available.',
        [{ text: 'Continue', onPress: () => router.replace('/(tabs)') }]
      );
    } finally {
      setIsLoading(false);
    }
  };

  function formatPhoneNumber(digits: string) {
    const part1 = digits.slice(0, 3);
    const part2 = digits.slice(3, 6);
    const part3 = digits.slice(6, 10);
    if (digits.length === 0) return '';
    if (digits.length < 4) return `(${part1}`;
    if (digits.length < 7) return `(${part1}) ${part2}`;
    return `(${part1}) ${part2}-${part3}`;
  }

  const handlePhoneChange = (input: string) => {
    const digits = input.replace(/\D/g, '').slice(0, 10);
    setRawPhoneNumber(digits);
  };

  const renderProfileStep = () => (
    <Animated.View 
      style={[
        styles.stepContainer,
        {
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }],
        },
      ]}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.logoContainer}>
          <Image 
            source={require('@/assets/images/coffee-character.png')} 
            style={styles.logoImage}
            contentFit="contain"
          />
        </View>
        <Text style={styles.welcomeTitle}>Welcome to Coffy!</Text>
        <Text style={styles.welcomeSubtitle}>
          Let's set up your profile so Joe can help coordinate with your friends
        </Text>
      </View>

      {/* Form */}
      <View style={styles.form}>
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Your Name</Text>
          <View style={styles.inputWrapper}>
            <TextInput
              style={styles.input}
              value={name}
              onChangeText={setName}
              placeholder="Enter your full name"
              placeholderTextColor={colors.textLight}
              autoCapitalize="words"
              maxLength={50}
            />
          </View>
          <Text style={styles.hint}>This is how you'll appear when Joe sends messages</Text>
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Phone Number</Text>
          <View style={styles.inputWrapper}>
            <TextInput
              style={styles.input}
              value={formatPhoneNumber(rawPhoneNumber)}
              onChangeText={handlePhoneChange}
              placeholder="(123) 456-7890"
              placeholderTextColor={colors.textLight}
              keyboardType="number-pad"
              maxLength={14}
            />
          </View>
          <Text style={styles.hint}>Joe will use this to coordinate coffee meetups</Text>
        </View>
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity 
          style={styles.continueButton} 
          onPress={handleProfileComplete}
        >
          <Text style={styles.continueButtonText}>Next: Load Contacts</Text>
        </TouchableOpacity>
      </View>
    </Animated.View>
  );

  const renderContactsStep = () => (
    <Animated.View 
      style={[
        styles.stepContainer,
        {
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }],
        },
      ]}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.logoContainer}>
          <Image 
            source={require('@/assets/images/coffee-character.png')} 
            style={styles.logoImage}
            contentFit="contain"
          />
        </View>
        <Text style={styles.welcomeTitle}>Load Your Contacts</Text>
        <Text style={styles.welcomeSubtitle}>
          Joe needs access to your contacts to help coordinate coffee meetups with your friends
        </Text>
      </View>

      {/* Contacts Status */}
      <View style={styles.contactsStatus}>
        {contacts.length > 0 ? (
          <View style={styles.contactsSuccess}>
            <Text style={styles.contactsSuccessIcon}>✅</Text>
            <Text style={styles.contactsSuccessText}>
              {contacts.length} contacts loaded!
            </Text>
            <Text style={styles.contactsSuccessSubtext}>
              Joe can now help coordinate with your friends
            </Text>
          </View>
        ) : (
          <View style={styles.contactsPrompt}>
            <Text style={styles.contactsPromptIcon}>📱</Text>
            <Text style={styles.contactsPromptText}>
              Ready to load your contacts?
            </Text>
            <Text style={styles.contactsPromptSubtext}>
              This helps Joe know who to coordinate with for coffee meetups
            </Text>
          </View>
        )}
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        {contacts.length === 0 ? (
          <TouchableOpacity 
            style={[styles.continueButton, contactsLoading && styles.continueButtonDisabled]} 
            onPress={hasContactsPermission ? loadContacts : requestContactsPermission}
            disabled={contactsLoading}
          >
            {contactsLoading ? (
              <ActivityIndicator size="small" color={colors.coffeeWhite} />
            ) : (
              <Text style={styles.continueButtonText}>
                {hasContactsPermission ? 'Load Contacts' : 'Allow Access to Contacts'}
              </Text>
            )}
          </TouchableOpacity>
        ) : (
          <TouchableOpacity 
            style={styles.continueButton} 
            onPress={proceedToComplete}
          >
            <Text style={styles.continueButtonText}>Continue Setup</Text>
          </TouchableOpacity>
        )}
      </View>
    </Animated.View>
  );

  const renderCompleteStep = () => (
    <Animated.View 
      style={[
        styles.stepContainer,
        {
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }],
        },
      ]}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.logoContainer}>
          <Image 
            source={require('@/assets/images/coffee-character.png')} 
            style={styles.logoImage}
            contentFit="contain"
          />
        </View>
        <Text style={styles.welcomeTitle}>All Set!</Text>
        <Text style={styles.welcomeSubtitle}>
          Your profile is ready and Joe has access to your contacts. Time to start coordinating coffee!
        </Text>
      </View>

      {/* Summary */}
      <View style={styles.summary}>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryIcon}>👤</Text>
          <Text style={styles.summaryText}>Profile: {name}</Text>
        </View>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryIcon}>📞</Text>
          <Text style={styles.summaryText}>Phone: {formatPhoneNumber(rawPhoneNumber)}</Text>
        </View>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryIcon}>📱</Text>
          <Text style={styles.summaryText}>Contacts: {contacts.length} loaded</Text>
        </View>
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity 
          style={[styles.continueButton, isLoading && styles.continueButtonDisabled]} 
          onPress={completeSetup}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator size="small" color={colors.coffeeWhite} />
          ) : (
            <Text style={styles.continueButtonText}>Enter Coffy</Text>
          )}
        </TouchableOpacity>
      </View>
    </Animated.View>
  );

  React.useEffect(() => {
    if (currentStep === 'contacts') {
      checkContactsPermission();
    }
  }, [currentStep]);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.background} />
      
      <KeyboardAvoidingView 
        style={styles.content}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {/* Progress Indicator */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View style={[
              styles.progressFill,
              {
                width: currentStep === 'profile' ? '33%' : 
                       currentStep === 'contacts' ? '66%' : '100%'
              }
            ]} />
          </View>
          <Text style={styles.progressText}>
            Step {currentStep === 'profile' ? '1' : currentStep === 'contacts' ? '2' : '3'} of 3
          </Text>
        </View>

        {currentStep === 'profile' && renderProfileStep()}
        {currentStep === 'contacts' && renderContactsStep()}
        {currentStep === 'complete' && renderCompleteStep()}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
  },
  progressContainer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  progressBar: {
    width: '100%',
    height: 4,
    backgroundColor: colors.coffeeCream,
    borderRadius: 2,
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.coffeeDark,
    borderRadius: 2,
  },
  progressText: {
    fontSize: 14,
    color: colors.textLight,
    fontWeight: '500',
  },
  stepContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 48,
  },
  logoContainer: {
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
  logoImage: {
    width: 70,
    height: 70,
  },
  welcomeTitle: {
    fontSize: 32,
    fontWeight: '700',
    color: colors.coffeeDark,
    textAlign: 'center',
    marginBottom: 12,
    letterSpacing: -0.8,
  },
  welcomeSubtitle: {
    fontSize: 17,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
    maxWidth: 300,
  },
  form: {
    gap: 32,
    marginBottom: 48,
  },
  inputGroup: {
    gap: 8,
  },
  label: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.coffeeDark,
    marginBottom: 4,
  },
  inputWrapper: {
    backgroundColor: colors.background,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: colors.coffeeCream,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
    height: 48,
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  input: {
    fontSize: 17,
    color: colors.textPrimary,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
  },
  hint: {
    fontSize: 14,
    color: colors.textLight,
    lineHeight: 20,
    marginTop: 4,
  },
  contactsStatus: {
    alignItems: 'center',
    marginBottom: 48,
  },
  contactsSuccess: {
    alignItems: 'center',
    backgroundColor: colors.coffeeCream,
    borderRadius: 20,
    padding: 24,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  contactsSuccessIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  contactsSuccessText: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.coffeeDark,
    textAlign: 'center',
    marginBottom: 8,
  },
  contactsSuccessSubtext: {
    fontSize: 16,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  contactsPrompt: {
    alignItems: 'center',
    backgroundColor: colors.coffeeCream,
    borderRadius: 20,
    padding: 24,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  contactsPromptIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  contactsPromptText: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.coffeeDark,
    textAlign: 'center',
    marginBottom: 8,
  },
  contactsPromptSubtext: {
    fontSize: 16,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  summary: {
    backgroundColor: colors.coffeeCream,
    borderRadius: 20,
    padding: 24,
    marginBottom: 48,
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  summaryItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  summaryIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  summaryText: {
    fontSize: 16,
    color: colors.coffeeDark,
    fontWeight: '500',
  },
  actions: {
    gap: 16,
  },
  continueButton: {
    backgroundColor: colors.coffeeDark,
    borderRadius: 16,
    paddingVertical: 18,
    alignItems: 'center',
    shadowColor: colors.coffeeDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
  },
  continueButtonDisabled: {
    backgroundColor: colors.coffeeLight,
    shadowOpacity: 0.1,
  },
  continueButtonText: {
    fontSize: 17,
    fontWeight: '600',
    color: colors.coffeeWhite,
  },
}); 