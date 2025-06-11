import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Alert } from 'react-native';
import * as WebBrowser from 'expo-web-browser';
import * as SecureStore from 'expo-secure-store';
import { router } from 'expo-router';


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
    syncProfileFromServer: () => Promise<boolean>;
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
            // Use the correct endpoint that matches where profile data is saved
            const response = await fetchWithTimeout(`${BACKEND_URL}/auth/users/profile/${userIdToCheck}`);
            
            if (response.status === 404) {
                // Try alternative endpoint pattern in case the API uses a different structure
                try {
                    const altResponse = await fetchWithTimeout(`${BACKEND_URL}/auth/user/${userIdToCheck}`);
                    if (altResponse.ok) {
                        const profileData = await altResponse.json();
                        const hasProfile = profileData.name && profileData.phone_number;
                        const hasContacts = profileData.contacts_loaded || false;
                        const needsSetup = !(hasProfile && hasContacts);
                        
                        console.log('Server profile check result (alt endpoint):', {
                            hasProfile,
                            hasContacts, 
                            needsSetup,
                            profileData: { name: profileData.name, phone: !!profileData.phone_number, contacts_loaded: profileData.contacts_loaded }
                        });
                        
                        return needsSetup;
                    }
                } catch (altError) {
                    console.log('Alternative endpoint also not available');
                }
                
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
                    console.log('=== GOOGLE LOGIN SUCCESS ===');
                    console.log('User ID:', userId);
                    console.log('Email:', email);
                    console.log('Name:', name);
                    
                    let needsSetup = true; // Default to needing setup for new users
                    
                    // Try to check if this is a new user or needs profile setup
                    try {
                        console.log('Checking if user needs profile setup...');
                        needsSetup = await checkProfileCompletion(userId);
                        console.log('Profile completion check during login result:', needsSetup);
                        
                        if (!needsSetup) {
                            console.log('✅ Existing user with complete profile - skipping setup');
                        } else {
                            console.log('📝 New user or incomplete profile - will show setup');
                        }
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
                    console.log('=========================');
                    
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
            
            // Navigate back to login screen
            router.replace('/');
        } catch (error) {
            console.error('Error clearing user data:', error);
            // Even if there's an error clearing data, still try to navigate to login
            try {
                router.replace('/');
            } catch (navError) {
                console.error('Error navigating to login:', navError);
            }
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

    const syncProfileFromServer = async (): Promise<boolean> => {
        if (!user?.id) {
            console.log('No user ID available for profile sync');
            return false;
        }

        try {
            console.log('🔄 Syncing profile from server for user:', user.id);
            
            // Try the primary endpoint first
            let response = await fetchWithTimeout(`${BACKEND_URL}/auth/users/profile/${user.id}`);
            
            // If that fails, try the alternative endpoint
            if (response.status === 404) {
                console.log('Primary endpoint not found, trying alternative...');
                response = await fetchWithTimeout(`${BACKEND_URL}/auth/user/${user.id}`);
            }
            
            if (response.ok) {
                const serverProfile = await response.json();
                console.log('📥 Server profile data:', serverProfile);
                
                // Check if the server has complete profile data
                const hasProfile = serverProfile.name && serverProfile.phone_number;
                const hasContacts = serverProfile.contacts_loaded || false;
                
                if (hasProfile) {
                    // Update user data with server information
                    const updatedUser: User = {
                        ...user,
                        name: serverProfile.name,
                        needsProfileSetup: !(hasProfile && hasContacts),
                        contactsLoaded: hasContacts
                    };
                    
                    // Update both state and storage
                    await updateUser(updatedUser);
                    
                    // Also save detailed profile data locally for offline access
                    await SecureStore.setItemAsync('userProfile', JSON.stringify({
                        name: serverProfile.name,
                        phone_number: serverProfile.phone_number,
                        user_id: user.id,
                        contacts_loaded: hasContacts
                    }));
                    
                    console.log('✅ Profile synced successfully from server');
                    console.log('Updated user:', updatedUser);
                    return true;
                } else {
                    console.log('⚠️ Server profile exists but is incomplete');
                    return false;
                }
            } else {
                console.log('❌ Server profile not found or error:', response.status);
                return false;
            }
        } catch (error) {
            console.error('💥 Error syncing profile from server:', error);
            return false;
        }
    };

    return (
        <AuthContext.Provider value={{ user, loading, handleGoogleLogin, signOut, checkProfileCompletion, updateUser, syncProfileFromServer }}>
            {children}
        </AuthContext.Provider>
    );
};

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within an AuthProvider');
    return context;
}