import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { useAuth } from '@/contexts/AuthContext';
import * as SecureStore from 'expo-secure-store';

/**
 * DEBUG COMPONENT - Add this temporarily to any screen to test profile syncing
 * 
 * To use: 
 * 1. Import this component: import DebugProfileComponent from './DEBUG_PROFILE_COMPONENT';
 * 2. Add <DebugProfileComponent /> to any screen
 * 3. Use the buttons to test profile functionality
 * 4. Remove when debugging is complete
 */

export default function DebugProfileComponent() {
    const { user, checkProfileCompletion, syncProfileFromServer, updateUser } = useAuth();

    const debugCheckProfile = async () => {
        try {
            if (!user?.id) {
                Alert.alert('Debug', 'No user ID available');
                return;
            }
            
            console.log('🔍 Manual profile completion check...');
            const needsSetup = await checkProfileCompletion(user.id);
            Alert.alert(
                'Profile Check Result', 
                `User needs profile setup: ${needsSetup}\n\nCheck console for detailed logs.`
            );
        } catch (error) {
            console.error('Debug profile check error:', error);
            Alert.alert('Debug Error', `Error: ${error.message}`);
        }
    };

    const debugSyncFromServer = async () => {
        try {
            console.log('🔄 Manual server sync...');
            const success = await syncProfileFromServer();
            Alert.alert(
                'Server Sync Result', 
                `Sync successful: ${success}\n\nCheck console for detailed logs.`
            );
        } catch (error) {
            console.error('Debug server sync error:', error);
            Alert.alert('Debug Error', `Error: ${error.message}`);
        }
    };

    const debugShowStoredData = async () => {
        try {
            const storedUser = await SecureStore.getItemAsync('user');
            const storedProfile = await SecureStore.getItemAsync('userProfile');
            const storedContacts = await SecureStore.getItemAsync('userContacts');
            
            console.log('=== STORED DATA DEBUG ===');
            console.log('User:', storedUser ? JSON.parse(storedUser) : 'None');
            console.log('Profile:', storedProfile ? JSON.parse(storedProfile) : 'None');
            console.log('Contacts count:', storedContacts ? JSON.parse(storedContacts).length : 0);
            console.log('========================');
            
            const contactsCount = storedContacts ? JSON.parse(storedContacts).length : 0;
            Alert.alert(
                'Stored Data', 
                `User: ${storedUser ? 'Found' : 'None'}\nProfile: ${storedProfile ? 'Found' : 'None'}\nContacts: ${contactsCount}\n\nCheck console for full details.`
            );
        } catch (error) {
            console.error('Debug storage error:', error);
            Alert.alert('Debug Error', `Error: ${error.message}`);
        }
    };

    const debugForceProfileSetup = async () => {
        try {
            if (!user) {
                Alert.alert('Debug', 'No user available');
                return;
            }
            
            const updatedUser = { ...user, needsProfileSetup: true };
            await updateUser(updatedUser);
            Alert.alert('Debug', 'Forced needsProfileSetup to true. Restart app to see profile setup screen.');
        } catch (error) {
            console.error('Debug force setup error:', error);
            Alert.alert('Debug Error', `Error: ${error.message}`);
        }
    };

    const debugPhoneNumberIssue = async () => {
        try {
            console.log('🔍 Debugging phone number issue...');
            
            // Check what's in local storage
            const storedProfile = await SecureStore.getItemAsync('userProfile');
            console.log('Local profile:', storedProfile ? JSON.parse(storedProfile) : 'None');
            
            // Try to sync from server
            const syncSuccess = await syncProfileFromServer();
            console.log('Server sync result:', syncSuccess);
            
            // Check again after sync
            const storedProfileAfter = await SecureStore.getItemAsync('userProfile');
            console.log('Local profile after sync:', storedProfileAfter ? JSON.parse(storedProfileAfter) : 'None');
            
            const profileData = storedProfileAfter ? JSON.parse(storedProfileAfter) : null;
            const phoneNumber = profileData?.phone_number || 'Not found';
            
            Alert.alert(
                'Phone Number Debug', 
                `Local phone number: ${phoneNumber}\nServer sync: ${syncSuccess ? 'Success' : 'Failed'}\n\nCheck console for full details.`
            );
        } catch (error) {
            console.error('Debug phone number error:', error);
            Alert.alert('Debug Error', `Error: ${error.message}`);
        }
    };

    if (!user) {
        return (
            <View style={styles.container}>
                <Text style={styles.title}>🐛 Debug Profile</Text>
                <Text style={styles.info}>No user logged in</Text>
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <Text style={styles.title}>🐛 Debug Profile</Text>
            <Text style={styles.info}>
                User: {user.name || user.email}{'\n'}
                ID: {user.id}{'\n'}
                Needs Setup: {user.needsProfileSetup ? 'Yes' : 'No'}
            </Text>
            
            <TouchableOpacity style={styles.button} onPress={debugCheckProfile}>
                <Text style={styles.buttonText}>Check Profile Completion</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.button} onPress={debugSyncFromServer}>
                <Text style={styles.buttonText}>Sync from Server</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.button} onPress={debugShowStoredData}>
                <Text style={styles.buttonText}>Show Stored Data</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.button} onPress={debugForceProfileSetup}>
                <Text style={styles.buttonText}>Force Profile Setup</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.button} onPress={debugPhoneNumberIssue}>
                <Text style={styles.buttonText}>Debug Phone Number Issue</Text>
            </TouchableOpacity>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        margin: 20,
        padding: 15,
        backgroundColor: '#f0f0f0',
        borderRadius: 8,
        borderWidth: 2,
        borderColor: '#ff6b6b',
    },
    title: {
        fontSize: 16,
        fontWeight: 'bold',
        marginBottom: 10,
        color: '#ff6b6b',
    },
    info: {
        fontSize: 12,
        marginBottom: 15,
        color: '#333',
    },
    button: {
        backgroundColor: '#ff6b6b',
        padding: 10,
        borderRadius: 5,
        marginBottom: 8,
    },
    buttonText: {
        color: 'white',
        textAlign: 'center',
        fontSize: 12,
        fontWeight: 'bold',
    },
}); 