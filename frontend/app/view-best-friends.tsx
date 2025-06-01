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
  Linking
} from 'react-native';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useAuth } from '@/contexts/AuthContext';

const BACKEND_URL = "http://localhost:8000";

interface BestFriend {
  id: string;
  name: string;
  phoneNumbers?: { number: string }[];
  emails?: { email: string }[];
}

export default function ViewBestFriendsScreen() {
  const { user } = useAuth();
  const [bestFriends, setBestFriends] = useState<BestFriend[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBestFriends();
  }, []);

  const loadBestFriends = async () => {
    if (!user) return;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/contacts/best-friends/list/${user.id}`);
      const data = await response.json();
      
      if (data.success) {
        setBestFriends(data.best_friends);
      }
    } catch (error) {
      console.error('Error loading best friends:', error);
      Alert.alert('Error', 'Failed to load best friends.');
    } finally {
      setLoading(false);
    }
  };

  const goBack = () => {
    router.back();
  };

  const callFriend = (phoneNumber: string) => {
    Linking.openURL(`tel:${phoneNumber}`);
  };

  const textFriend = (phoneNumber: string) => {
    Linking.openURL(`sms:${phoneNumber}`);
  };

  const emailFriend = (email: string) => {
    Linking.openURL(`mailto:${email}`);
  };

  const renderBestFriend = ({ item }: { item: BestFriend }) => {
    const phoneNumber = item.phoneNumbers?.[0]?.number || '';
    const email = item.emails?.[0]?.email || '';

    return (
      <View style={styles.friendCard}>
        <View style={styles.friendInfo}>
          <View style={styles.friendAvatar}>
            <Text style={styles.friendInitial}>
              {item.name.charAt(0).toUpperCase()}
            </Text>
          </View>
          <View style={styles.friendDetails}>
            <Text style={styles.friendName}>{item.name}</Text>
            {phoneNumber ? (
              <Text style={styles.friendContact}>{phoneNumber}</Text>
            ) : null}
            {email ? (
              <Text style={styles.friendContact}>{email}</Text>
            ) : null}
          </View>
        </View>
        
        <View style={styles.actionButtons}>
          {phoneNumber && (
            <>
              <TouchableOpacity 
                style={styles.actionButton} 
                onPress={() => callFriend(phoneNumber)}
              >
                <Text style={styles.actionButtonText}>📞</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={styles.actionButton} 
                onPress={() => textFriend(phoneNumber)}
              >
                <Text style={styles.actionButtonText}>💬</Text>
              </TouchableOpacity>
            </>
          )}
          {email && (
            <TouchableOpacity 
              style={styles.actionButton} 
              onPress={() => emailFriend(email)}
            >
              <Text style={styles.actionButtonText}>📧</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <StatusBar barStyle="dark-content" backgroundColor="#F5E6D3" />
        
        <View style={styles.header}>
          <Text style={styles.headerTitle}>My Best Friends</Text>
          <TouchableOpacity style={styles.backButton} onPress={goBack}>
            <Text style={styles.backButtonText}>←</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#8B4513" />
          <Text style={styles.loadingText}>Loading best friends...</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#F5E6D3" />
      
      <View style={styles.header}>
        <Text style={styles.headerTitle}>My Best Friends</Text>
        <TouchableOpacity style={styles.backButton} onPress={goBack}>
          <Text style={styles.backButtonText}>←</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.summaryContainer}>
        <Image 
          source={require('@/assets/images/coffee-hello.png')} 
          style={styles.coffeeIcon}
          contentFit="contain"
        />
        <Text style={styles.summaryText}>
          You have {bestFriends.length} best friend{bestFriends.length === 1 ? '' : 's'} ☕
        </Text>
        <Text style={styles.summarySubtext}>
          Ready for coffee chats anytime!
        </Text>
      </View>

      {bestFriends.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyStateText}>No best friends selected yet</Text>
          <Text style={styles.emptyStateSubtext}>
            Go back and select your favorite people for coffee chats!
          </Text>
          <TouchableOpacity 
            style={styles.selectButton} 
            onPress={() => router.push('/best-friends')}
          >
            <Text style={styles.selectButtonText}>Select Best Friends</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <>
          <FlatList
            data={bestFriends}
            renderItem={renderBestFriend}
            keyExtractor={(item) => item.id}
            style={styles.friendsList}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ paddingBottom: 20 }}
          />

          <View style={styles.bottomActions}>
            <TouchableOpacity 
              style={styles.editButton} 
              onPress={() => router.push('/best-friends')}
            >
              <Text style={styles.editButtonText}>✏️ Edit Best Friends</Text>
            </TouchableOpacity>
          </View>
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
  summaryContainer: {
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
  summaryText: {
    fontSize: 18,
    color: '#8B4513',
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 5,
  },
  summarySubtext: {
    fontSize: 14,
    color: '#8B4513',
    opacity: 0.8,
    textAlign: 'center',
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
  friendsList: {
    flex: 1,
    paddingHorizontal: 20,
  },
  friendCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
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
  friendInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  friendAvatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#8B4513',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 15,
  },
  friendInitial: {
    color: '#F5E6D3',
    fontSize: 18,
    fontWeight: 'bold',
  },
  friendDetails: {
    flex: 1,
  },
  friendName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8B4513',
    marginBottom: 4,
  },
  friendContact: {
    fontSize: 14,
    color: '#8B4513',
    opacity: 0.7,
  },
  actionButtons: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  actionButton: {
    backgroundColor: '#8B4513',
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 8,
  },
  actionButtonText: {
    fontSize: 18,
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
    fontWeight: '600',
    marginBottom: 10,
    textAlign: 'center',
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#8B4513',
    opacity: 0.8,
    textAlign: 'center',
    marginBottom: 30,
  },
  selectButton: {
    backgroundColor: '#8B4513',
    paddingVertical: 15,
    paddingHorizontal: 30,
    borderRadius: 25,
    alignItems: 'center',
  },
  selectButtonText: {
    color: '#F5E6D3',
    fontWeight: '600',
    fontSize: 16,
  },
  bottomActions: {
    padding: 20,
  },
  editButton: {
    backgroundColor: '#8B4513',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 20,
    alignItems: 'center',
  },
  editButtonText: {
    color: '#F5E6D3',
    fontWeight: '600',
    fontSize: 16,
  },
}); 