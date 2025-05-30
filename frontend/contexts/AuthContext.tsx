import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Alert } from 'react-native';
import * as WebBrowser from 'expo-web-browser';
import * as SecureStore from 'expo-secure-store';


// User type
export type User = {
    id: string;
    email: string;
    name: string | null;
};

// AuthContext type
interface AuthContextType {
    user: User | null;
    loading: boolean;
    handleGoogleLogin: () => Promise<void>;
    signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);
const BACKEND_URL = "http://localhost:8000";

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Load user from secure storage on mount
        const loadUser = async () => {
            try {
                const userJson = await SecureStore.getItemAsync('user');
                if (userJson) {
                    setUser(JSON.parse(userJson));
                }
            } catch (e) {
                console.error('Failed to load user from storage', e);
            } finally {
                setLoading(false);
            }
        };
        loadUser();
    }, []);

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
                    const userData: User = { id: userId, email, name };
                    setUser(userData);
                    await SecureStore.setItemAsync('user', JSON.stringify(userData));
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
        <AuthContext.Provider value={{ user, loading, handleGoogleLogin, signOut }}>
            {children}
        </AuthContext.Provider>
    );
};

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within an AuthProvider');
    return context;
}