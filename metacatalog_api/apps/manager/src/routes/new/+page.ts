import type { PageLoad } from './$types';
import type { License, Variable, Author } from '$lib/models';
import { buildApiUrl, devFetch, devLog } from '$lib/stores/settingsStore';

export const load: PageLoad = async ({ fetch }) => {
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