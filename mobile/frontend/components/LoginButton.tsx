import { TouchableOpacity, Text, StyleSheet, View } from "react-native";
import React from "react";
import { useAuth } from '@/contexts/AuthContext';

export default function LoginButton() {
    const { user, handleGoogleLogin, loading } = useAuth();

    if (loading) {
        return (
            <View style={styles.container}>
                <Text style={styles.buttonText}>Loading...</Text>
            </View>
        );
    }

    return (
        <>
        {user ? (
            <View style={styles.container}>
                <Text style={styles.buttonText}>Logged in as: {user.email}</Text>
            </View>
        ) : (
            <TouchableOpacity style={styles.button} onPress={handleGoogleLogin}>
                <Text style={styles.buttonText}>Login with Google</Text>
            </TouchableOpacity>
        )}
        </>
    );
}

const styles = StyleSheet.create({
    container: {
        backgroundColor: "#fdf7eb",
        paddingVertical: 12,
        paddingHorizontal: 24,
        borderRadius: 8,
        borderWidth: 1,
        borderColor: "#000000",
        alignItems: "center",
        margin: 10,
    },
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