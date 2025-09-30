import type { PageLoad } from './$types';
import { buildApiUrl, createDevFetch, devLog } from '$lib/stores/settingsStore';

// Disable SSR - this will run only on the client side
export const ssr = false;

export const load: PageLoad = async ({ fetch, params }) => {
    // Create devFetch that uses Svelte's enhanced fetch function
    const devFetch = createDevFetch(fetch);
    
    try {
        // Get the dataset ID from URL parameters
        const datasetId = params.id;
        
        if (!datasetId) {
            throw new Error('Dataset ID is required');
        }
        
        // Build the API URL for the specific dataset
        const datasetUrl = buildApiUrl(`/entries/${datasetId}`);
        
        devLog.info('Fetching dataset from', datasetUrl);
        
        const datasetResponse = await devFetch(datasetUrl);
        let dataset: any = null;
        
        if (datasetResponse.ok) {
            dataset = await datasetResponse.json();
            devLog.info(`Loaded dataset with ID: ${datasetId}`);
        } else if (datasetResponse.status === 404) {
            devLog.info(`Dataset with ID ${datasetId} not found`);
        } else {
            devLog.error('Failed to fetch dataset', { 
                status: datasetResponse.status,
                statusText: datasetResponse.statusText 
            });
        }

        return {
            dataset,
            datasetId,
            notFound: datasetResponse.status === 404
        };
    } catch (error) {
        devLog.error('Error in dataset page load', error);
        return {
            dataset: null,
            datasetId: params.id,
            notFound: true,
            error: error instanceof Error ? error.message : 'Unknown error'
        };
    }
};
