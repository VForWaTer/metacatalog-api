import type { PageLoad } from './$types';
import { buildApiUrl, createDevFetch, devLog } from '$lib/stores/settingsStore';

// Disable SSR - this will run only on the client side
export const ssr = false;

export const load: PageLoad = async ({ fetch, url }) => {
    // Create devFetch that uses Svelte's enhanced fetch function
    const devFetch = createDevFetch(fetch);
    
    try {
        // Get search parameter from URL
        const searchQuery = url.searchParams.get('search') || '';
        
        // Build the API URL with search parameter if provided
        let entriesUrl = buildApiUrl('/entries');
        if (searchQuery) {
            entriesUrl += `?search=${encodeURIComponent(searchQuery)}`;
        }
        
        devLog.info('Fetching entries from', entriesUrl);
        
        const entriesResponse = await devFetch(entriesUrl);
        let entries: any[] = [];
        
        if (entriesResponse.ok) {
            entries = await entriesResponse.json();
            devLog.info(`Loaded ${entries.length} entries`);
        } else {
            devLog.error('Failed to fetch entries', { status: entriesResponse.status });
        }

        return {
            entries,
            searchQuery
        };
    } catch (error) {
        devLog.error('Error in page load', error);
        return {
            entries: [],
            searchQuery: ''
        };
    }
};
