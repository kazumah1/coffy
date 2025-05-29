import { TouchableOpacity, Text, StyleSheet } from "react-native";
import * as WebBrowser from "expo-web-browser";

export default function LoginButton() {
    function handleGoogleLogin() {
        WebBrowser.openBrowserAsync("http://localhost:8000/auth/google/login");
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
    elevation: 2, // for Android shadow
    shadowColor: "#000", // for iOS shadow
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