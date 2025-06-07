import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Alert } from 'react-native';
import * as WebBrowser from 'expo-web-browser';
import * as SecureStore from 'expo-secure-store';


// User type
export type User = {
    id: string;
    email: string;
    name: string | null;
    needsProfileSetup?: boolean;
    contactsLoaded?: boolean;
};

// AuthContext type
interface AuthContextType {
    user: User | null;
    loading: boolean;
    handleGoogleLogin: () => Promise<void>;
    signOut: () => Promise<void>;
    checkProfileCompletion: () => Promise<boolean>;
    updateUser: (userData: User) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);
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

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    // Debug helper function
    const debugStoredData = async () => {
        try {
            const storedUser = await SecureStore.getItemAsync('user');
            const storedProfile = await SecureStore.getItemAsync('userProfile');
            console.log('=== DEBUG STORED DATA ===');
            console.log('Stored user:', storedUser ? JSON.parse(storedUser) : 'None');
            console.log('Stored profile:', storedProfile ? JSON.parse(storedProfile) : 'None');
            console.log('========================');
        } catch (error) {
            console.error('Error debugging stored data:', error);
        }
    };

    useEffect(() => {
        // Load user from secure storage on mount
        const loadUser = async () => {
            try {   
                // Debug what's in storage first
                await debugStoredData();
                
                // Always try to load from storage, not just if user exists
                const storedUser = await SecureStore.getItemAsync('user');
                if (storedUser) {
                    const userData = JSON.parse(storedUser);
                    console.log('Loaded user from storage:', userData);
                    
                    // ALWAYS set the user first - authentication is separate from profile completion
                    setUser(userData);
                    
                    // Only check profile completion if it's not already marked as complete
                    // This is now optional and won't affect authentication
                    if (userData.id && userData.needsProfileSetup !== false) {
                        try {
                            const needsSetup = await checkProfileCompletion(userData.id);
                            if (needsSetup !== userData.needsProfileSetup) {
                                const updatedUser = { ...userData, needsProfileSetup: needsSetup };
                                console.log('Updating profile setup status:', needsSetup);
                                setUser(updatedUser);
                                // Update stored user with profile setup flag
                                await SecureStore.setItemAsync('user', JSON.stringify(updatedUser));
                            }
                        } catch (profileError) {
                            // Profile completion check failed, but user stays logged in
                            console.warn('Profile completion check failed, user remains logged in:', profileError);
                        }
                    }
                } else {
                    console.log('No user found in storage');
                }
            } catch (e) {
                console.error('Failed to load user from storage', e);
            } finally {
                setLoading(false);
            }
        };
        loadUser();
    }, []);

    const checkProfileCompletion = async (userId?: string): Promise<boolean> => {
        const userIdToCheck = userId || user?.id;
        if (!userIdToCheck) return true;

        try {
            console.log('Checking profile completion for user:', userIdToCheck);
            const response = await fetchWithTimeout(`${BACKEND_URL}/auth/user/${userIdToCheck}`);
            
            if (response.status === 404) {
                // Backend endpoint doesn't exist yet - check local storage as fallback
                console.log('Backend not available, checking local profile completion');
                try {
                    const localProfile = await SecureStore.getItemAsync('userProfile');
                    const localContacts = await SecureStore.getItemAsync('userContacts');
                    if (localProfile) {
                        const profileData = JSON.parse(localProfile);
                        const hasProfile = profileData.name && profileData.phone_number;
                        const hasContacts = localContacts && JSON.parse(localContacts).length > 0;
                        const needsSetup = !(hasProfile && hasContacts);
                        console.log('Local profile check result:', needsSetup);
                        return needsSetup;
                    }
                } catch (localError) {
                    console.error('Error checking local profile:', localError);
                }
                // If we can't check either way, assume setup is needed for new users
                return true; 
            }
            
            if (response.ok) {
                console.log('Backend available, checking server-side profile completion');
                const profileData = await response.json();
                
                // Check if user has completed essential profile info and loaded contacts
                const hasProfile = profileData.name && profileData.phone_number;
                const hasContacts = profileData.contacts_loaded || false;
                const needsSetup = !(hasProfile && hasContacts);
                
                console.log('Server profile check result:', {
                    hasProfile,
                    hasContacts, 
                    needsSetup,
                    profileData: { name: profileData.name, phone: !!profileData.phone_number, contacts_loaded: profileData.contacts_loaded }
                });
                
                return needsSetup;
            } else {
                console.warn('Profile completion check failed with status:', response.status);
                // If server is available but returns error, don't assume setup is needed
                // This prevents disrupting existing users due to server errors
                return false;
            }
        } catch (error) {
            console.error('Error checking profile completion:', error);
            // On error, default to not needing setup to avoid disrupting existing users
            // New users will be handled by the login flow
            return false;
        }
    };

    async function handleGoogleLogin() {
        try {
            const result = await WebBrowser.openAuthSessionAsync(
                `${BACKEND_URL}/auth/google/login`,
                `${BACKEND_URL}/auth/google/callback`
            );

            if (result.type === "success") {
                const url = new URL(result.url);
                const email = url.searchParams.get("email");
                const userId = url.searchParams.get("user_id");
                const name = url.searchParams.get("name");
                
                if (email && userId) {
                    let needsSetup = true; // Default to needing setup for new users
                    
                    // Try to check if this is a new user or needs profile setup
                    try {
                        needsSetup = await checkProfileCompletion(userId);
                        console.log('Profile completion check during login:', needsSetup);
                    } catch (profileError) {
                        console.warn('Profile completion check failed during login, defaulting to setup needed:', profileError);
                        // Default to needing setup for safety with new users
                        needsSetup = true;
                    }
                    
                    const userData: User = { 
                        id: userId, 
                        email, 
                        name,
                        needsProfileSetup: needsSetup
                    };
                    
                    // Save user data to secure storage for persistence FIRST
                    await SecureStore.setItemAsync('user', JSON.stringify(userData));
                    console.log('User data saved to storage:', userData);
                    
                    // Then set the user state
                    setUser(userData);
                    Alert.alert("Success", "Logged in successfully!");
                } else {
                    Alert.alert("Error", "Missing user info in callback");
                }
            }
        } catch (error) {
            Alert.alert("Error", "Failed to complete login");
            console.error(error);
        }
    }

    async function signOut() {
        try {
            setUser(null);
            // Clear all user-related data from storage
            await SecureStore.deleteItemAsync('user');
            await SecureStore.deleteItemAsync('userProfile');
            await SecureStore.deleteItemAsync('userContacts');
            await SecureStore.deleteItemAsync('userBestFriends');
            await SecureStore.deleteItemAsync('userAvailabilityStatus');
            console.log('All user data cleared from storage');
        } catch (error) {
            console.error('Error clearing user data:', error);
        }
    }

    const updateUser = async (userData: User) => {
        try {
            setUser(userData);
            await SecureStore.setItemAsync('user', JSON.stringify(userData));
            console.log('User data updated and saved to storage:', userData);
        } catch (error) {
            console.error('Error updating user data:', error);
        }
    };

    return (
        <AuthContext.Provider value={{ user, loading, handleGoogleLogin, signOut, checkProfileCompletion, updateUser }}>
            {children}
        </AuthContext.Provider>
    );
};

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within an AuthProvider');
    return context;
}