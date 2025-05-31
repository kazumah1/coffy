import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  FlatList, 
  TouchableOpacity, 
  StyleSheet, 
  StatusBar,
  Alert,
  ActivityIndicator
} from 'react-native';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useAuth } from '@/contexts/AuthContext';

const BACKEND_URL = "http://localhost:8000";

interface Contact {
  id: string;
  name: string;
  phoneNumbers?: { number: string }[];
  emails?: { email: string }[];
}

interface BestFriend extends Contact {
  isBestFriend: boolean;
}

export default function BestFriendsScreen() {
  const { user } = useAuth();
  const [contacts, setContacts] = useState<BestFriend[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedCount, setSelectedCount] = useState(0);

  useEffect(() => {
    loadContactsAndBestFriends();
  }, []);

  const loadContactsAndBestFriends = async () => {
    if (!user) return;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/contacts/best-friends/${user.id}`);
      const data = await response.json();
      
      if (data.success) {
        setContacts(data.contacts);
        setSelectedCount(data.contacts.filter((c: BestFriend) => c.isBestFriend).length);
      }
    } catch (error) {
      console.error('Error loading contacts and best friends:', error);
      Alert.alert('Error', 'Failed to load contacts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleBestFriend = (contactId: string) => {
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
    
    setSaving(true);
    try {
      const bestFriends = contacts.filter(contact => contact.isBestFriend);
      
      const response = await fetch(`${BACKEND_URL}/api/contacts/best-friends/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user.id,
          best_friends: bestFriends
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        Alert.alert(
          'Success!', 
          `Saved ${selectedCount} best friends! Now you can easily plan coffee chats with them.`,
          [
            {
              text: 'OK',
              onPress: () => router.back()
            }
          ]
        );
      } else {
        Alert.alert('Error', 'Failed to save best friends. Please try again.');
      }
    } catch (error) {
      console.error('Error saving best friends:', error);
      Alert.alert('Error', 'Failed to save best friends. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const goBack = () => {
    router.back();
  };

  const renderContact = ({ item }: { item: BestFriend }) => {
    const phoneNumber = item.phoneNumbers?.[0]?.number || '';
    const email = item.emails?.[0]?.email || '';

    return (
      <TouchableOpacity 
        style={[
          styles.contactItem,
          item.isBestFriend && styles.selectedContactItem
        ]}
        onPress={() => toggleBestFriend(item.id)}
      >
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
        <View style={styles.selectionIndicator}>
          {item.isBestFriend ? (
            <View style={styles.selectedIndicator}>
              <Text style={styles.checkmark}>✓</Text>
            </View>
          ) : (
            <View style={styles.unselectedIndicator} />
          )}
        </View>
      </TouchableOpacity>
    );
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <StatusBar barStyle="dark-content" backgroundColor="#F5E6D3" />
        
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Best Friends</Text>
          <TouchableOpacity style={styles.backButton} onPress={goBack}>
            <Text style={styles.backButtonText}>←</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#8B4513" />
          <Text style={styles.loadingText}>Loading contacts...</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#F5E6D3" />
      
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Best Friends</Text>
        <TouchableOpacity style={styles.backButton} onPress={goBack}>
          <Text style={styles.backButtonText}>←</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.instructionsContainer}>
        <Image 
          source={require('@/assets/images/coffee-hello.png')} 
          style={styles.coffeeIcon}
          contentFit="contain"
        />
        <Text style={styles.instructionsText}>
          Select your best friends to make planning coffee chats even easier!
        </Text>
        <Text style={styles.selectedCountText}>
          {selectedCount} friends selected
        </Text>
      </View>

      <FlatList
        data={contacts}
        renderItem={renderContact}
        keyExtractor={(item) => item.id}
        style={styles.contactsList}
        showsVerticalScrollIndicator={false}
      />

      <View style={styles.actionContainer}>
        <TouchableOpacity 
          style={[
            styles.saveButton,
            saving && styles.saveButtonDisabled
          ]} 
          onPress={saveBestFriends}
          disabled={saving}
        >
          {saving ? (
            <ActivityIndicator size="small" color="#F5E6D3" />
          ) : (
            <Text style={styles.saveButtonText}>
              Save Best Friends ({selectedCount})
            </Text>
          )}
        </TouchableOpacity>
      </View>
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
  instructionsContainer: {
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#FFFFFF',
    marginHorizontal: 20,
    marginVertical: 15,
    borderRadius: 15,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 3,
  },
  coffeeIcon: {
    width: 60,
    height: 60,
    marginBottom: 10,
  },
  instructionsText: {
    fontSize: 16,
    color: '#8B4513',
    textAlign: 'center',
    marginBottom: 10,
    lineHeight: 22,
  },
  selectedCountText: {
    fontSize: 14,
    color: '#8B4513',
    fontWeight: '600',
    opacity: 0.8,
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
  selectedContactItem: {
    backgroundColor: '#FFF8DC',
    borderWidth: 2,
    borderColor: '#8B4513',
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
  selectionIndicator: {
    marginLeft: 10,
  },
  selectedIndicator: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#8B4513',
    alignItems: 'center',
    justifyContent: 'center',
  },
  unselectedIndicator: {
    width: 30,
    height: 30,
    borderRadius: 15,
    borderWidth: 2,
    borderColor: '#8B4513',
    backgroundColor: 'transparent',
  },
  checkmark: {
    color: '#F5E6D3',
    fontSize: 16,
    fontWeight: 'bold',
  },
  actionContainer: {
    padding: 20,
    backgroundColor: '#F5E6D3',
  },
  saveButton: {
    backgroundColor: '#8B4513',
    paddingVertical: 15,
    paddingHorizontal: 30,
    borderRadius: 25,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  saveButtonDisabled: {
    opacity: 0.7,
  },
  saveButtonText: {
    color: '#F5E6D3',
    fontWeight: '600',
    fontSize: 16,
  },
}); 