# SvelteKit Fetch Function Improvements

## Overview

This document outlines the improvements made to the SvelteKit application to properly handle the `fetch` function and ensure all API calls use the enhanced SvelteKit fetch capabilities.

## Issues Addressed

### 1. **devFetch Not Using SvelteKit's Enhanced Fetch**

**Problem**: The original `devFetch` function was using `window.fetch` instead of SvelteKit's enhanced `fetch` function, losing benefits like:
- Server-side rendering (SSR) support
- Relative URL handling
- Cookie forwarding
- Request deduplication

**Solution**: Implemented a `createDevFetch` function that accepts the SvelteKit fetch function as a parameter:

```typescript
// settingsStore.ts
export function createDevFetch(svelteKitFetch: typeof fetch) {
    globalFetch = svelteKitFetch;
    return devFetch;
}
```

**Usage in +page.ts**:
```typescript
export const load: PageLoad = async ({ fetch }) => {
    // Create devFetch that uses Svelte's enhanced fetch function
    const devFetch = createDevFetch(fetch);
    
    // Now all devFetch calls use SvelteKit's fetch
    const response = await devFetch(url);
};
```

### 2. **Missing Library Structure**

**Problem**: The application was importing from non-existent `$lib/*` paths, causing build failures.

**Solution**: Created complete library structure:
- `$lib/stores/settingsStore.ts` - Settings and fetch utilities
- `$lib/stores/metadataStore.ts` - Form state management
- `$lib/models/index.ts` - TypeScript interfaces
- `$lib/components/OrcidLookup.svelte` - ORCID search component
- `$lib/services/metadataService.ts` - API service layer

### 3. **Inconsistent Fetch Usage**

**Problem**: Some components made fetch calls without using the `devFetch` wrapper, missing development logging.

**Solution**: 
- **ORCID Lookup**: Now uses `devFetch` for all external API calls to ORCID
- **Metadata Service**: All CRUD operations use `devFetch` for consistent logging
- **Form Submission**: POST requests for saving metadata use the service layer

## Implementation Details

### Enhanced devFetch Function

```typescript
export async function devFetch(
    input: RequestInfo | URL, 
    init?: RequestInit
): Promise<Response> {
    const fetchFn = globalFetch || globalThis.fetch;
    
    if (dev) {
        const url = typeof input === 'string' ? input : input.toString();
        const method = init?.method || 'GET';
        devLog.info(`${method} ${url}`);
        
        if (init?.body) {
            devLog.info('Request body:', init.body);
        }
    }
    
    try {
        const response = await fetchFn(input, init);
        
        if (dev) {
            const url = typeof input === 'string' ? input : input.toString();
            devLog.info(`Response ${response.status} ${response.statusText} for ${url}`);
        }
        
        return response;
    } catch (error) {
        if (dev) {
            const url = typeof input === 'string' ? input : input.toString();
            devLog.error(`Fetch error for ${url}:`, error);
        }
        throw error;
    }
}
```

### Metadata Service with devFetch

```typescript
export class MetadataService {
    static async createEntry(entry: MetadataEntryCreate): Promise<MetadataEntry> {
        const url = buildApiUrl('/entries');
        const response = await devFetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(entry)
        });
        // ... error handling and response processing
    }
}
```

### ORCID Component with devFetch

The `OrcidLookup` component now uses `devFetch` for:
- Searching ORCID database: `https://pub.orcid.org/v3.0/search`
- Fetching author details: `https://pub.orcid.org/v3.0/{orcid-id}`

## Benefits Achieved

### 1. **Proper SvelteKit Integration**
- All fetch calls now use SvelteKit's enhanced fetch function
- SSR compatibility maintained
- Relative URLs work correctly in all environments

### 2. **Development Experience**
- Consistent logging for all API calls in development mode
- Request/response details logged automatically
- Error tracking improved

### 3. **Type Safety**
- Complete TypeScript interfaces for all data models
- Type-safe API service methods
- Proper error handling with typed responses

### 4. **Maintainable Architecture**
- Clear separation between stores, services, and components
- Reusable service layer for all API interactions
- Centralized fetch configuration

## Usage Examples

### In Page Load Functions
```typescript
export const load: PageLoad = async ({ fetch }) => {
    const devFetch = createDevFetch(fetch);
    
    const licensesUrl = buildApiUrl('/licenses');
    const response = await devFetch(licensesUrl);
    return await response.json();
};
```

### In Components
```typescript
import { MetadataService } from '$lib/services/metadataService';

// This automatically uses devFetch internally
const result = await MetadataService.createEntry(entryData);
```

### For External APIs
```typescript
// ORCID lookup automatically uses devFetch
const response = await devFetch('https://pub.orcid.org/v3.0/search?q=...', {
    headers: { 'Accept': 'application/json' }
});
```

## Migration Notes

If you have existing components that use `fetch` directly:

1. **For page load functions**: Use `createDevFetch(fetch)` pattern
2. **For component API calls**: Use the service layer (`MetadataService`, etc.)
3. **For external APIs**: Import and use `devFetch` directly

## Testing

The implementation preserves all SvelteKit fetch features while adding development logging. Test both:
- Development mode (logging should appear)
- Production mode (no logging, but fetch still works)
- SSR scenarios (fetch should work server-side)

## Files Modified/Created

### Created:
- `metacatalog_api/apps/manager/src/lib/stores/settingsStore.ts`
- `metacatalog_api/apps/manager/src/lib/stores/metadataStore.ts`
- `metacatalog_api/apps/manager/src/lib/models/index.ts`
- `metacatalog_api/apps/manager/src/lib/models.ts`
- `metacatalog_api/apps/manager/src/lib/components/OrcidLookup.svelte`
- `metacatalog_api/apps/manager/src/lib/services/metadataService.ts`

### Modified:
- `metacatalog_api/apps/manager/src/routes/new/+page.ts` - Now uses `createDevFetch`
- `metacatalog_api/apps/manager/src/routes/new/+page.svelte` - Added save functionality and imports

This solution ensures that all fetch operations properly use SvelteKit's enhanced fetch function while maintaining development logging capabilities.