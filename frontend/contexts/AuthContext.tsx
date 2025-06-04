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

    useEffect(() => {
        // Load user from secure storage on mount
        const loadUser = async () => {
            try {   
                if (user) {
                    setUser(user);
                    
                    // Check if user needs profile setup
                    if (user.id && !user.needsProfileSetup) {
                        const needsSetup = await checkProfileCompletion(user.id);
                        if (needsSetup) {
                            const updatedUser = { ...user, needsProfileSetup: true };
                            setUser(updatedUser);
                        }
                    }
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
            const response = await fetchWithTimeout(`${BACKEND_URL}/auth/user/${userIdToCheck}`);
            
            if (response.status === 404) {
                // Backend endpoint doesn't exist yet - check local storage
                console.log('Backend not available, checking local profile completion');
                try {
                    const localProfile = await SecureStore.getItemAsync('userProfile');
                    const localContacts = await SecureStore.getItemAsync('userContacts');
                    if (localProfile) {
                        const profileData = JSON.parse(localProfile);
                        const hasProfile = profileData.name && profileData.phone_number;
                        const hasContacts = localContacts && JSON.parse(localContacts).length > 0;
                        return !(hasProfile && hasContacts);
                    }
                } catch (localError) {
                    console.error('Error checking local profile:', localError);
                }
                return true; // Default to needing setup if we can't check
            }
            
            if (response.ok) {
                console.log('Backend available, checking profile completion');
                const profileData = await response.json();
                // Check if user has completed essential profile info and loaded contacts
                const hasProfile = profileData.name && profileData.phone_number;
                const hasContacts = profileData.contacts_loaded || false;
                return !(hasProfile && hasContacts);
            }
        } catch (error) {
            console.error('Error checking profile completion:', error);
            return true; // Default to needing setup if we can't verify
        }
        return true; // Default to needing setup if we can't verify
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
                    // Check if this is a new user or needs profile setup
                    const needsSetup = await checkProfileCompletion(userId);
                    
                    const userData: User = { 
                        id: userId, 
                        email, 
                        name,
                        needsProfileSetup: needsSetup
                    };
                    
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
        setUser(null);
        await SecureStore.deleteItemAsync('user');
    }

    return (
        <AuthContext.Provider value={{ user, loading, handleGoogleLogin, signOut, checkProfileCompletion }}>
            {children}
        </AuthContext.Provider>
    );
};

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within an AuthProvider');
    return context;
}