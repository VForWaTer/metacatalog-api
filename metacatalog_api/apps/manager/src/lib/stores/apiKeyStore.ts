import { writable } from 'svelte/store';

// Store for API key management
export const apiKey = writable<string>('');

// Store for API key status
export const apiKeyStatus = writable<'unknown' | 'valid' | 'invalid' | 'checking'>('unknown');

// Function to validate API key
export async function validateApiKey(key: string, backendUrl: string): Promise<boolean> {
    if (!key) return false;
    
    try {
        const response = await fetch(`${backendUrl}/validate`, {
            method: 'GET',
            headers: {
                'X-API-Key': key
            }
        });
        
        // If we get a 200, the key is valid
        if (response.status === 200) {
            const result = await response.json();
            console.log('🔑 Token validation successful:', result);
            return true;
        }
        
        // If we get a 401, the key is invalid
        if (response.status === 401) {
            console.log('🔑 Token validation failed: Invalid token');
            return false;
        }
        
        // Any other status code is considered invalid
        console.log('🔑 Token validation failed: Unexpected status', response.status);
        return false;
    } catch (error) {
        console.error('🔑 Error validating API key:', error);
        return false;
    }
}

// Function to check if we're running on localhost
export function isLocalhost(): boolean {
    if (typeof window === 'undefined') return false;
    return window.location.hostname === 'localhost' || 
           window.location.hostname === '127.0.0.1' ||
           window.location.hostname.startsWith('192.168.');
}

// Function to get default admin key for localhost
export function getDefaultAdminKey(): string {
    // Check for admin token in environment variable first
    if (typeof window !== 'undefined' && import.meta.env.VITE_METACATALOG_ADMIN_TOKEN) {
        return import.meta.env.VITE_METACATALOG_ADMIN_TOKEN;
    }
    
    // Fallback to localStorage if available
    if (typeof window !== 'undefined') {
        const storedToken = localStorage.getItem('metacatalog_admin_token');
        if (storedToken) {
            return storedToken;
        }
    }
    
    // For localhost, we'll use a placeholder that can be replaced
    // with a real admin token when the database is set up
    return 'admin-localhost-dev-key';
}

// Function to store admin token in localStorage
export function storeAdminToken(token: string): void {
    if (typeof window !== 'undefined') {
        localStorage.setItem('metacatalog_admin_token', token);
        console.log('🔑 Admin token stored in localStorage');
    }
}

// Function to clear admin token from localStorage
export function clearAdminToken(): void {
    if (typeof window !== 'undefined') {
        localStorage.removeItem('metacatalog_admin_token');
        console.log('🔑 Admin token cleared from localStorage');
    }
} 