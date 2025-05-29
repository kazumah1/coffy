import { TouchableOpacity, Text, StyleSheet, Alert } from "react-native";
import * as WebBrowser from "expo-web-browser";
import React, { useState } from "react";

const BACKEND_URL = "http://localhost:8000";

export default function LoginButton() {
    const [userEmail, setUserEmail] = useState<string | null>(null);

    async function handleGoogleLogin() {
        try {
            const result = await WebBrowser.openAuthSessionAsync(
                `${BACKEND_URL}/auth/google/login`,
                `${BACKEND_URL}/auth/google/callback`
            );

            if (result.type === "success") {
                // Parse the URL to get the user info
                const url = new URL(result.url);
                const email = url.searchParams.get("email");
                if (email) {
                    setUserEmail(email);
                    Alert.alert("Success", "Logged in successfully!");
                }
            }
        } catch (error) {
            Alert.alert("Error", "Failed to complete login");
            console.error(error);
        }
    }

    if (userEmail) {
        return (
            <TouchableOpacity style={styles.button}>
                <Text style={styles.buttonText}>Logged in as: {userEmail}</Text>
            </TouchableOpacity>
        );
    }

    return (
        <TouchableOpacity style={styles.button} onPress={handleGoogleLogin}>
            <Text style={styles.buttonText}>Login with Google</Text>
        </TouchableOpacity>
    );
}

const styles = StyleSheet.create({
    button: {
        backgroundColor: "#fdf7eb",
        paddingVertical: 12,
        paddingHorizontal: 24,
        borderRadius: 8,
        borderWidth: 1,
        borderColor: "#000000",
        alignItems: "center",
        margin: 10,
        elevation: 2,
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.2,
        shadowRadius: 2,
    },
    buttonText: {
        color: "#000000",
        fontWeight: "regular",
        fontSize: 16,
    },
});