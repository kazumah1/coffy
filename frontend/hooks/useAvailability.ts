import { useState, useEffect } from 'react'

const BACKEND_URL = process.env.BACKEND_URL;

export async function fetchAvailability(userId: string, startDate: string, endDate: string) {
    const response = await fetch(`${BACKEND_URL}/availability/${userId}?start_date=${startDate}&end_date=${endDate}`)
    const data = await response.json();
    return { ok: response.ok, statusText: response.statusText, data };
}

export function useAvailability(userId: string, startDate: string, endDate: string) {
    const [availability, setAvailability] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetchAvailability(userId, startDate, endDate)
                if (!response.ok) {
                    setError(response.statusText)
                    setLoading(false)
                    setAvailability(null)
                } else {
                    setAvailability(response.data)
                    setLoading(false)
                }
            } catch (error: any) {
                setError(error.message || String(error))
                setLoading(false)
                setAvailability(null)
            }
        }
        fetchData()
    }, [userId, startDate, endDate])

    return { availability, loading, error }
}