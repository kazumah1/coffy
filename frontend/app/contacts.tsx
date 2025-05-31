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
  TextInput
} from 'react-native';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import * as Contacts from 'expo-contacts';
import { useAuth } from '@/contexts/AuthContext';

const BACKEND_URL = "http://localhost:8000";

interface Contact {
  id: string;
  name: string;
  phoneNumbers?: { number: string }[];
  emails?: { email: string }[];
}

export default function ContactsScreen() {
  const { user } = useAuth();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [filteredContacts, setFilteredContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasPermission, setHasPermission] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [savedContactsCount, setSavedContactsCount] = useState(0);

  useEffect(() => {
    checkPermission();
    if (user) {
      checkSavedContacts();
    }
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

  const checkPermission = async () => {
    const { status } = await Contacts.getPermissionsAsync();
    setHasPermission(status === 'granted');
  };

  const requestContactsPermission = async () => {
    const { status } = await Contacts.requestPermissionsAsync();
    if (status === 'granted') {
      setHasPermission(true);
      loadContacts();
    } else {
      Alert.alert(
        'Permission Required',
        'We need access to your contacts to help you plan coffee chats with friends.',
        [{ text: 'OK' }]
      );
    }
  };

  const loadContacts = async () => {
    setLoading(true);
    try {
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
      
      // Sync contacts with backend
      if (user) {
        const syncSuccess = await syncContactsWithBackend(formattedContacts);
        
        // Show success message
        if (syncSuccess) {
          Alert.alert(
            'Success! ☕',
            `Loaded and saved ${formattedContacts.length} contacts to your account. You can now select your best friends!`,
            [{ text: 'OK' }]
          );
        } else {
          Alert.alert(
            'Contacts Loaded ⚠️',
            `Loaded ${formattedContacts.length} contacts but could not save to server. Please check your connection and try again.`,
            [{ text: 'OK' }]
          );
        }
      } else {
        Alert.alert(
          'Success! ☕',
          `Loaded ${formattedContacts.length} contacts!`,
          [{ text: 'OK' }]
        );
      }
    } catch (error) {
      console.error('Error loading contacts:', error);
      Alert.alert('Error', 'Failed to load contacts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const syncContactsWithBackend = async (contactsList: Contact[]) => {
    try {
      console.log(`Syncing ${contactsList.length} contacts to backend...`);
      
      const response = await fetch(`${BACKEND_URL}/api/contacts/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user?.id,
          contacts: contactsList
        }),
      });

      const data = await response.json();
      
      if (response.ok && data.success) {
        console.log(`✅ Successfully synced ${contactsList.length} contacts to database`);
        // Refresh saved contacts count
        setSavedContactsCount(contactsList.length);
        return true;
      } else {
        console.error('❌ Failed to sync contacts:', data.message || 'Unknown error');
        Alert.alert(
          'Sync Warning',
          'Contacts loaded but may not be saved to server. Please try again if you want to select best friends.',
          [{ text: 'OK' }]
        );
        return false;
      }
    } catch (error) {
      console.error('❌ Error syncing contacts with backend:', error);
      Alert.alert(
        'Sync Warning', 
        'Contacts loaded but could not connect to server. Best friends feature may not work until contacts are synced.',
        [{ text: 'OK' }]
      );
      return false;
    }
  };

  const checkSavedContacts = async () => {
    if (!user) return;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/contacts/best-friends/${user.id}`);
      const data = await response.json();
      
      if (data.success) {
        setSavedContactsCount(data.contacts.length);
      }
    } catch (error) {
      console.log('Could not check saved contacts:', error);
    }
  };

  const goBack = () => {
    router.back();
  };

  const navigateToBestFriends = () => {
    router.push('/best-friends');
  };

  const renderContact = ({ item }: { item: Contact }) => {
    const phoneNumber = item.phoneNumbers?.[0]?.number || '';
    const email = item.emails?.[0]?.email || '';

    return (
      <TouchableOpacity style={styles.contactItem}>
        <View style={styles.contactAvatar}>
          <Text style={styles.contactInitial}>
            {item.name.charAt(0).toUpperCase()}
          </Text>
        </View>
        <View style={styles.contactInfo}>
          <Text style={styles.contactName}>{item.name}</Text>
          {phoneNumber ? (
            <Text style={styles.contactDetail}>{phoneNumber}</Text>
          ) : null}
          {email ? (
            <Text style={styles.contactDetail}>{email}</Text>
          ) : null}
        </View>
      </TouchableOpacity>
    );
  };

  if (!hasPermission) {
    return (
      <View style={styles.container}>
        <StatusBar barStyle="dark-content" backgroundColor="#F5E6D3" />
        
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Contacts</Text>
          <TouchableOpacity style={styles.backButton} onPress={goBack}>
            <Text style={styles.backButtonText}>←</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.permissionContainer}>
          <Image 
            source={require('@/assets/images/coffee-hello.png')} 
            style={styles.coffeeCharacter}
            contentFit="contain"
          />
          
          <Text style={styles.permissionTitle}>Access Your Contacts</Text>
          <Text style={styles.permissionDescription}>
            We need access to your contacts to help you plan amazing coffee chats with your friends and family!
          </Text>
          
          <TouchableOpacity 
            style={styles.permissionButton} 
            onPress={requestContactsPermission}
          >
            <Text style={styles.permissionButtonText}>Allow Access</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#F5E6D3" />
      
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Contacts</Text>
        <TouchableOpacity style={styles.backButton} onPress={goBack}>
          <Text style={styles.backButtonText}>←</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search contacts..."
          placeholderTextColor="#8B4513"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>

      {contacts.length === 0 && !loading ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyStateText}>No contacts found</Text>
          {savedContactsCount > 0 && (
            <Text style={styles.databaseStatusText}>
              📊 {savedContactsCount} contacts saved in database
            </Text>
          )}
          <TouchableOpacity style={styles.loadButton} onPress={loadContacts}>
            <Text style={styles.loadButtonText}>Load Contacts</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <>
          {savedContactsCount > 0 && (
            <View style={styles.databaseStatus}>
              <Text style={styles.databaseStatusText}>
                📊 Database: {savedContactsCount} contacts saved
              </Text>
              <TouchableOpacity 
                style={styles.refreshButton} 
                onPress={checkSavedContacts}
              >
                <Text style={styles.refreshButtonText}>↻ Refresh</Text>
              </TouchableOpacity>
            </View>
          )}
          
          <View style={styles.actionsContainer}>
            <TouchableOpacity 
              style={styles.bestFriendsButton} 
              onPress={navigateToBestFriends}
            >
              <Text style={styles.bestFriendsButtonText}>Select Best Friends ☕</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.viewBestFriendsButton} 
              onPress={() => router.push('/view-best-friends')}
            >
              <Text style={styles.viewBestFriendsButtonText}>👥 View My Best Friends</Text>
            </TouchableOpacity>
          </View>

          {loading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#8B4513" />
              <Text style={styles.loadingText}>Loading contacts...</Text>
            </View>
          ) : (
            <FlatList
              data={filteredContacts}
              renderItem={renderContact}
              keyExtractor={(item) => item.id}
              style={styles.contactsList}
              showsVerticalScrollIndicator={false}
            />
          )}
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5E6D3',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 50,
    paddingBottom: 10,
    paddingHorizontal: 20,
    backgroundColor: '#8B4513',
    position: 'relative',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#F5E6D3',
  },
  backButton: {
    position: 'absolute',
    left: 20,
    top: 50,
    padding: 5,
  },
  backButtonText: {
    fontSize: 24,
    color: '#F5E6D3',
    fontWeight: 'bold',
  },
  permissionContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  coffeeCharacter: {
    width: 150,
    height: 150,
    marginBottom: 30,
  },
  permissionTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#8B4513',
    textAlign: 'center',
    marginBottom: 15,
  },
  permissionDescription: {
    fontSize: 16,
    color: '#8B4513',
    textAlign: 'center',
    marginBottom: 30,
    paddingHorizontal: 20,
    lineHeight: 22,
  },
  permissionButton: {
    backgroundColor: '#8B4513',
    paddingVertical: 15,
    paddingHorizontal: 30,
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
  permissionButtonText: {
    color: '#F5E6D3',
    fontWeight: '600',
    fontSize: 16,
  },
  searchContainer: {
    padding: 20,
  },
  searchInput: {
    backgroundColor: '#FFFFFF',
    borderRadius: 25,
    paddingHorizontal: 20,
    paddingVertical: 12,
    fontSize: 16,
    color: '#8B4513',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  actionsContainer: {
    paddingHorizontal: 20,
    paddingBottom: 10,
  },
  bestFriendsButton: {
    backgroundColor: '#8B4513',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 20,
    alignItems: 'center',
  },
  bestFriendsButtonText: {
    color: '#F5E6D3',
    fontWeight: '600',
    fontSize: 16,
  },
  viewBestFriendsButton: {
    backgroundColor: '#8B4513',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 20,
    alignItems: 'center',
    marginLeft: 10,
  },
  viewBestFriendsButtonText: {
    color: '#F5E6D3',
    fontWeight: '600',
    fontSize: 16,
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  emptyStateText: {
    fontSize: 18,
    color: '#8B4513',
    marginBottom: 20,
  },
  loadButton: {
    backgroundColor: '#8B4513',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 20,
  },
  loadButtonText: {
    color: '#F5E6D3',
    fontWeight: '600',
    fontSize: 16,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  loadingText: {
    fontSize: 16,
    color: '#8B4513',
    marginTop: 10,
  },
  contactsList: {
    flex: 1,
    paddingHorizontal: 20,
  },
  contactItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 15,
    marginVertical: 5,
    borderRadius: 15,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  contactAvatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#8B4513',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 15,
  },
  contactInitial: {
    color: '#F5E6D3',
    fontSize: 18,
    fontWeight: 'bold',
  },
  contactInfo: {
    flex: 1,
  },
  contactName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8B4513',
    marginBottom: 4,
  },
  contactDetail: {
    fontSize: 14,
    color: '#8B4513',
    opacity: 0.7,
  },
  databaseStatus: {
    backgroundColor: '#8B4513',
    padding: 10,
    borderRadius: 10,
    marginHorizontal: 20,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  databaseStatusText: {
    color: '#F5E6D3',
    fontWeight: '600',
    fontSize: 14,
    flex: 1,
  },
  refreshButton: {
    backgroundColor: '#F5E6D3',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 15,
    alignItems: 'center',
  },
  refreshButtonText: {
    color: '#8B4513',
    fontWeight: '600',
    fontSize: 12,
  },
}); 