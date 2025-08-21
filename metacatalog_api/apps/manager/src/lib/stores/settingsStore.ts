import { writable } from 'svelte/store';

// Development mode detection
const isDev = (): boolean => {
    if (typeof window !== 'undefined') {
        // Browser environment - check for Vite dev mode
        return import.meta.env.DEV || false;
    } else {
        // Server environment - assume development for now
        // In production, this would be handled by SvelteKit's build process
        return true;
    }
};

// Get backend URL from environment variable or fall back to default
const getBackendUrl = (): string => {
    // Since we disabled SSR, this will only run in the browser
    // Browser environment - check for Vite environment variable
    return import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001';
};

// Settings store interface
export interface Settings {
    backendUrl: string;
    isDev: boolean;
}

// Create the settings store with initial values
export const settings = writable<Settings>({
    backendUrl: getBackendUrl(),
    isDev: isDev()
});

// Helper function to get the current backend URL
export const getBackendUrlFromStore = (): string => {
    let currentSettings: Settings | undefined;
    settings.subscribe(value => {
        currentSettings = value;
    })();
    return currentSettings?.backendUrl || 'http://localhost:8001';
};

// Helper function to build API URLs
export const buildApiUrl = (endpoint: string): string => {
    const baseUrl = getBackendUrlFromStore();
    // Ensure endpoint starts with /
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${baseUrl}${cleanEndpoint}`;
};

// Development logging utilities
export const devLog = {
    fetch: (url: string, options?: RequestInit, response?: Response, duration?: number) => {
        if (isDev()) {
            const timestamp = new Date().toISOString();
            const method = options?.method || 'GET';
            const status = response?.status;
            const statusText = response?.statusText;
            
            console.group(`🌐 [${timestamp}] ${method} ${url}`);
            
            if (options?.body) {
                console.log('📤 Request Body:', options.body);
            }
            
            if (response) {
                const statusColor = status && status < 400 ? '🟢' : '🔴';
                console.log(`${statusColor} Status: ${status} ${statusText}`);
                
                if (duration !== undefined) {
                    console.log(`⏱️  Duration: ${duration}ms`);
                }
            }
            
            console.groupEnd();
        }
    },
    
    error: (message: string, error?: any) => {
        if (isDev()) {
            console.error(`❌ ${message}`, error);
        }
    },
    
    info: (message: string, data?: any) => {
        if (isDev()) {
            console.info(`ℹ️  ${message}`, data);
        }
    }
};

// Global fetch function reference - will be set by createDevFetch
let globalFetch: typeof fetch = globalThis.fetch;

/**
 * Creates a devFetch function that uses the provided fetch function (e.g., Svelte's enhanced fetch)
 * This preserves Svelte's fetch features like SSR support and relative URLs
 */
export function createDevFetch(svelteKitFetch: typeof fetch) {
    globalFetch = svelteKitFetch;
    return devFetch;
}

// Enhanced fetch function with development logging
export const devFetch = async (url: string, options?: RequestInit): Promise<Response> => {
    const startTime = Date.now();
    const fetchFn = globalFetch || globalThis.fetch;
    
    try {
        const response = await fetchFn(url, options);
        const duration = Date.now() - startTime;
        
        devLog.fetch(url, options, response, duration);
        
        return response;
    } catch (error) {
        const duration = Date.now() - startTime;
        devLog.fetch(url, options, undefined, duration);
        devLog.error(`Fetch failed for ${url}`, error);
        throw error;
    }
}; 