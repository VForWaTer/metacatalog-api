# Fetch Implementation Analysis & Recommendations

## Issues Identified

### 1. SvelteKit Fetch vs devFetch in Page Load Functions

**Problem**: In `+page.ts`, you're using `devFetch` instead of the SvelteKit-provided `fetch` function. This means you're losing SvelteKit's benefits:
- Server-side rendering support
- Automatic response inlining during hydration
- Cookie forwarding
- Proper error handling for SSR/client transitions

**Current Implementation**:
```typescript
// In +page.ts
export const load: PageLoad = async ({ fetch }) => {
    // ❌ Using devFetch instead of the provided fetch
    const licensesResponse = await devFetch(licensesUrl);
    // ...
}
```

### 2. Missing Store Implementation

**Problem**: The code imports from `$lib/stores/settingsStore` but this file doesn't exist:
```typescript
import { buildApiUrl, devFetch, devLog } from '$lib/stores/settingsStore';
```

### 3. Missing Component Files

**Problem**: References to `OrcidLookup` component that doesn't exist:
```svelte
import OrcidLookup from '$lib/components/OrcidLookup.svelte';
```

## Recommended Solutions

### Solution 1: Create a Fetch Wrapper that Uses SvelteKit's Fetch

Create a higher-order function that wraps SvelteKit's fetch with your logging functionality:

**Create**: `src/lib/stores/settingsStore.ts`
```typescript
import { writable } from 'svelte/store';
import { dev } from '$app/environment';

// Settings store
export const settings = writable({
    isDev: dev,
    apiBaseUrl: 'http://localhost:8000/api'  // adjust as needed
});

// Dev logging utility
export const devLog = {
    info: (...args: any[]) => {
        if (dev) console.log('[API]', ...args);
    },
    error: (...args: any[]) => {
        if (dev) console.error('[API ERROR]', ...args);
    },
    warn: (...args: any[]) => {
        if (dev) console.warn('[API WARN]', ...args);
    }
};

// Build API URL helper
export function buildApiUrl(endpoint: string): string {
    const baseUrl = 'http://localhost:8000/api';  // TODO: make configurable
    return `${baseUrl}${endpoint}`;
}

// Create a fetch wrapper that accepts the SvelteKit fetch function
export function createDevFetch(svelteKitFetch: typeof fetch) {
    return async (url: string, options?: RequestInit): Promise<Response> => {
        if (dev) {
            devLog.info('Fetching:', url, options ? 'with options' : '');
        }
        
        try {
            const response = await svelteKitFetch(url, options);
            
            if (dev) {
                devLog.info(`Response ${response.status}:`, url);
            }
            
            return response;
        } catch (error) {
            if (dev) {
                devLog.error('Fetch failed:', url, error);
            }
            throw error;
        }
    };
}

// For client-side usage (when SvelteKit fetch is not available)
export const devFetch = createDevFetch(fetch);
```

### Solution 2: Update the Page Load Function

**Update**: `+page.ts`
```typescript
import type { PageLoad } from './$types';
import type { License, Variable, Author } from '$lib/models';
import { buildApiUrl, createDevFetch, devLog } from '$lib/stores/settingsStore';

export const load: PageLoad = async ({ fetch }) => {
    // ✅ Create devFetch using SvelteKit's fetch
    const devFetch = createDevFetch(fetch);
    
    try {
        // Fetch licenses
        const licensesUrl = buildApiUrl('/licenses');
        devLog.info('Fetching licenses from', licensesUrl);
        
        const licensesResponse = await devFetch(licensesUrl);
        let licenses: License[] = [];
        
        if (licensesResponse.ok) {
            licenses = await licensesResponse.json();
            devLog.info(`Loaded ${licenses.length} licenses`);
        } else {
            devLog.error('Failed to fetch licenses', { status: licensesResponse.status });
        }

        // Fetch variables
        const variablesUrl = buildApiUrl('/variables');
        devLog.info('Fetching variables from', variablesUrl);
        
        const variablesResponse = await devFetch(variablesUrl);
        let variables: Variable[] = [];
        
        if (variablesResponse.ok) {
            variables = await variablesResponse.json();
            devLog.info(`Loaded ${variables.length} variables`);
        } else {
            devLog.error('Failed to fetch variables', { status: variablesResponse.status });
        }

        // Fetch authors
        const authorsUrl = buildApiUrl('/authors');
        devLog.info('Fetching authors from', authorsUrl);
        
        const authorsResponse = await devFetch(authorsUrl);
        let authors: Author[] = [];
        
        if (authorsResponse.ok) {
            authors = await authorsResponse.json();
            devLog.info(`Loaded ${authors.length} authors`);
        } else {
            devLog.error('Failed to fetch authors', { status: authorsResponse.status });
        }

        return {
            licenses,
            variables,
            authors
        };
    } catch (error) {
        devLog.error('Error in page load', error);
        return {
            licenses: [],
            variables: [],
            authors: []
        };
    }
};
```

### Solution 3: Create Missing Components

**Create**: `src/lib/components/OrcidLookup.svelte` (Basic implementation)
```svelte
<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import type { AuthorCreate } from '$lib/models';
    import { devFetch, devLog } from '$lib/stores/settingsStore';

    const dispatch = createEventDispatcher<{
        authorFound: [AuthorCreate];
    }>();

    let orcidId = $state('');
    let isLoading = $state(false);
    let error = $state('');

    async function lookupOrcid() {
        if (!orcidId.trim()) return;
        
        isLoading = true;
        error = '';
        
        try {
            // Example ORCID API call (adjust URL as needed)
            const response = await devFetch(`https://pub.orcid.org/v3.0/${orcidId}/person`, {
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Transform ORCID data to your AuthorCreate format
                const author: AuthorCreate = {
                    first_name: data.name?.['given-names']?.value || '',
                    last_name: data.name?.['family-name']?.value || '',
                    is_organisation: false,
                    organisation_name: '',
                    organisation_abbrev: '',
                    affiliation: data.addresses?.address?.[0]?.country?.value || ''
                };
                
                dispatch('authorFound', [author]);
                orcidId = '';
            } else {
                error = 'ORCID not found or API error';
            }
        } catch (err) {
            devLog.error('ORCID lookup failed:', err);
            error = 'Failed to lookup ORCID';
        } finally {
            isLoading = false;
        }
    }
</script>

<div class="space-y-4">
    <div>
        <label for="orcid" class="block text-sm font-medium text-gray-700 mb-2">
            ORCID ID
        </label>
        <div class="flex gap-2">
            <input
                type="text"
                id="orcid"
                bind:value={orcidId}
                placeholder="0000-0000-0000-0000"
                class="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={isLoading}
            />
            <button
                type="button"
                onclick={lookupOrcid}
                disabled={isLoading || !orcidId.trim()}
                class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
                {isLoading ? 'Looking up...' : 'Lookup'}
            </button>
        </div>
        {#if error}
            <p class="mt-1 text-sm text-red-600">{error}</p>
        {/if}
    </div>
</div>
```

### Solution 4: Consistent Fetch Usage Throughout App

For client-side fetch calls (like form submissions), create a client-side fetch service:

**Create**: `src/lib/services/apiService.ts`
```typescript
import { buildApiUrl, devFetch, devLog } from '$lib/stores/settingsStore';
import type { MetadataEntry } from '$lib/models';

export class ApiService {
    // Save metadata entry
    static async saveMetadataEntry(entry: Partial<MetadataEntry>): Promise<MetadataEntry> {
        const url = buildApiUrl('/entries');
        devLog.info('Saving metadata entry:', entry);
        
        const response = await devFetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(entry)
        });
        
        if (!response.ok) {
            const error = await response.text();
            devLog.error('Failed to save entry:', error);
            throw new Error(`Failed to save entry: ${response.status}`);
        }
        
        const savedEntry = await response.json();
        devLog.info('Entry saved successfully:', savedEntry);
        return savedEntry;
    }
    
    // Add other API methods as needed...
}
```

## Additional Recommendations

1. **Create Missing Directory Structure**:
   ```
   src/
   ├── lib/
   │   ├── components/
   │   │   └── OrcidLookup.svelte
   │   ├── stores/
   │   │   ├── settingsStore.ts
   │   │   └── metadataStore.ts
   │   ├── services/
   │   │   └── apiService.ts
   │   └── models.ts
   ```

2. **Type Safety**: Ensure all API response types are properly defined in `models.ts`

3. **Error Handling**: Implement consistent error handling across all fetch calls

4. **Environment Configuration**: Make API URLs configurable based on environment

## Benefits of This Approach

1. ✅ Uses SvelteKit's fetch in load functions (preserves SSR benefits)
2. ✅ Consistent logging across all fetch calls
3. ✅ Centralized API configuration
4. ✅ Type-safe API calls
5. ✅ Easy to test and mock
6. ✅ Clear separation between server-side and client-side fetch usage

This solution maintains your dev logging functionality while properly integrating with SvelteKit's fetch system.