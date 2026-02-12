import { writable } from 'svelte/store';

// Initialize API key from localStorage if available
function getInitialApiKey(): string {
    if (typeof window !== 'undefined') {
        const stored = localStorage.getItem('metacatalog_api_key');
        if (stored) {
            return stored;
        }
    }
    return '';
}

// Store for API key management
export const apiKey = writable<string>(getInitialApiKey());

// Sync API key to localStorage whenever it changes
if (typeof window !== 'undefined') {
    apiKey.subscribe((value) => {
        if (value && value.trim() !== '') {
            localStorage.setItem('metacatalog_api_key', value);
        } else {
            localStorage.removeItem('metacatalog_api_key');
        }
    });
}

// Store for API key status
export const apiKeyStatus = writable<'unknown' | 'valid' | 'invalid' | 'checking'>('unknown');

// Modal visibility for token entry (open/close from anywhere)
export const tokenModalOpen = writable<boolean>(false);
export function openTokenModal(): void {
    tokenModalOpen.set(true);
}
export function closeTokenModal(): void {
    tokenModalOpen.set(false);
}

export function hasStoredToken(): boolean {
    if (typeof window === 'undefined') return false;
    const t = localStorage.getItem('metacatalog_api_key');
    return t !== null && t.trim() !== '';
}

// Function to validate API key
export async function validateApiKey(key: string, backendUrl: string): Promise<boolean> {
    if (!key || key.trim() === '') {
        console.log('Token validation failed: No API key provided');
        return false;
    }
    
    try {
        apiKeyStatus.set('checking');
        const response = await fetch(`${backendUrl}/validate`, {
            method: 'GET',
            headers: {
                'X-API-Key': key.trim()
            }
        });
        
        // If we get a 200, the key is valid
        if (response.status === 200) {
            const result = await response.json();
            console.log('Token validation successful:', result);
            apiKeyStatus.set('valid');
            // Store the validated key in the store (which will sync to localStorage)
            apiKey.set(key.trim());
            return true;
        }
        
        // If we get a 401, the key is invalid
        if (response.status === 401) {
            const errorData = await response.json().catch(() => ({ detail: 'Invalid API key' }));
            console.log('Token validation failed: Invalid token', errorData);
            apiKeyStatus.set('invalid');
            return false;
        }
        
        // Any other status code is considered invalid
        console.log('Token validation failed: Unexpected status', response.status);
        apiKeyStatus.set('invalid');
        return false;
    } catch (error) {
        console.error('Error validating API key:', error);
        apiKeyStatus.set('invalid');
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
        const storedToken = localStorage.getItem('metacatalog_api_key');
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
        localStorage.setItem('metacatalog_api_key', token);
        console.log('Admin token stored in localStorage');
    }
}

// Function to clear admin token from localStorage
export function clearAdminToken(): void {
    if (typeof window !== 'undefined') {
        localStorage.removeItem('metacatalog_api_key');
        console.log('Admin token cleared from localStorage');
    }
}

/** Sync apiKey store from localStorage when token exists and store is empty. Call from layout on init. */
export function syncApiKeyFromStorage(): void {
    if (typeof window === 'undefined') return;
    if (!hasStoredToken()) return;
    const stored = localStorage.getItem('metacatalog_api_key');
    if (stored) {
        apiKey.update((current) => (current ? current : stored));
    }
} 