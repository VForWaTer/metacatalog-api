import { browser } from '$app/environment';
import { base } from '$app/paths';

/**
 * Generate a path that works in both development and production
 * @param path - The path relative to the app root
 * @returns The full path with proper base prefix
 */
export function appPath(path: string): string {
    // Remove leading slash if present
    const cleanPath = path.startsWith('/') ? path.slice(1) : path;
    
    // In development, base is empty, so just return the path
    // In production, base is '/manager', so we need to include it
    return `${base}/${cleanPath}`.replace(/\/+/g, '/');
}

/**
 * Generate an external path (outside the SvelteKit app)
 * @param path - The external path
 * @returns The external path (unchanged)
 */
export function externalPath(path: string): string {
    return path;
}

/**
 * Check if we're in development mode
 */
export function isDevelopment(): boolean {
    return browser ? window.location.hostname === 'localhost' : false;
}
