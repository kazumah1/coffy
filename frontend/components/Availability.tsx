import { useAuth } from "@/contexts/AuthContext";
import { useAvailability } from "@/hooks/useAvailability";
import { Text, StyleSheet, View, FlatList } from "react-native";

// Define the event type
interface Event {
    summary: string;
    start: string;
    end: string;
    calendar_id: string;
}

type AvailabilityProps = { start: string, end: string }

export default function Availability(props: AvailabilityProps) {
    const { user } = useAuth()
    const { availability, loading, error } = useAvailability(user?.id ?? "", props.start, props.end);
    if (!user) {
        return <Text style={styles.wrappingText}>User not found</Text>
    }
    if (loading) {
        return <Text style={styles.wrappingText}>Loading...</Text>
    }
    if (error) {
        return <Text style={[styles.wrappingText, { color: 'red' }]}>Error: {typeof error === 'string' ? error : (error as any).message || String(error)}</Text>
    }
    const events: Event[] = Array.isArray(availability) ? availability : [];
    if (events.length === 0) {
        return <Text style={styles.wrappingText}>No events found in this range.</Text>
    }
    return (
        <View style={{ width: '100%' }}>
            <Text style={styles.wrappingText}>Events in this range:</Text>
            <FlatList
                data={events}
                keyExtractor={(_, idx) => idx.toString()}
                renderItem={({ item }) => (
                    <View style={styles.eventItem}>
                        <Text style={styles.eventTitle}>{item.summary}</Text>
                        <Text style={styles.eventTime}>Start: {item.start}</Text>
                        <Text style={styles.eventTime}>End: {item.end}</Text>
                        <Text style={styles.eventCalendar}>Calendar: {item.calendar_id}</Text>
                    </View>
                )}
            />
        </View>
    );
}

const styles = StyleSheet.create({
    wrappingText: {
        flexWrap: 'wrap',
        width: '100%',
        fontSize: 16,
        lineHeight: 22,
        textAlign: 'center',
        marginBottom: 10,
    },
    eventItem: {
        backgroundColor: '#fdf7eb',
        borderRadius: 8,
        padding: 10,
        marginVertical: 6,
        marginHorizontal: 10,
        borderWidth: 1,
        borderColor: '#ccc',
    },
    eventTitle: {
        fontWeight: 'bold',
        fontSize: 16,
        marginBottom: 2,
    },
    eventTime: {
        fontSize: 14,
    },
    eventCalendar: {
        fontSize: 12,
        color: '#888',
    },
});