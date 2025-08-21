<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import type { AuthorCreate } from '$lib/models';

    const dispatch = createEventDispatcher<{
        authorFound: [AuthorCreate];
    }>();

    // Local state
    let orcidId = $state('');
    let isLoading = $state(false);
    let error = $state<string | null>(null);
    let foundAuthor = $state<AuthorCreate | null>(null);

    // ORCID ID validation regex
    const orcidRegex = /^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]$/;

    // Check if ORCID ID is valid format
    const isValidOrcid = $derived(orcidRegex.test(orcidId));

    // Check if we should trigger lookup (valid format and long enough)
    const shouldLookup = $derived(isValidOrcid && orcidId.length === 19);

    // Interface for ORCID API responses
    interface OrcidPerson {
        name: {
            'given-names': { value: string };
            'family-name': { value: string };
        };
    }

    interface OrcidEmployment {
        'affiliation-group': Array<{
            summaries: Array<{
                'employment-summary': {
                    'department-name'?: string;
                    organization: {
                        name: string;
                    };
                };
            }>;
        }>;
    }

    // Fetch author data from ORCID
    async function lookupOrcid() {
        if (!shouldLookup) return;

        isLoading = true;
        error = null;
        foundAuthor = null;

        try {
            // Fetch person data
            const personResponse = await fetch(`https://pub.orcid.org/v3.0/${orcidId}/person`, {
                headers: {
                    'Accept': 'application/vnd.orcid+json'
                }
            });

            if (!personResponse.ok) {
                throw new Error(`Failed to fetch person data: ${personResponse.statusText}`);
            }

            const personData: OrcidPerson = await personResponse.json();

            // Fetch employment data for affiliation
            let affiliation = '';
            try {
                const employmentResponse = await fetch(`https://pub.orcid.org/v3.0/${orcidId}/employments`, {
                    headers: {
                        'Accept': 'application/vnd.orcid+json'
                    }
                });

                if (employmentResponse.ok) {
                    const employmentData: OrcidEmployment = await employmentResponse.json();
                    const currentEmployment = employmentData['affiliation-group']?.[0]?.summaries?.[0]?.['employment-summary'];
                    if (currentEmployment) {
                        affiliation = currentEmployment.organization.name;
                        if (currentEmployment['department-name']) {
                            affiliation += `, ${currentEmployment['department-name']}`;
                        }
                    }
                }
            } catch (empError) {
                // Employment data is optional, continue without it
                console.warn('Could not fetch employment data:', empError);
            }

            // Create author object
            const author: AuthorCreate = {
                first_name: personData.name['given-names'].value,
                last_name: personData.name['family-name'].value,
                is_organisation: false,
                organisation_name: '',
                organisation_abbrev: '',
                affiliation: affiliation
            };

            foundAuthor = author;
            
            // Auto-add to metadata store
            dispatch('authorFound', [author]);

        } catch (err) {
            error = err instanceof Error ? err.message : 'Unknown error occurred';
        } finally {
            isLoading = false;
        }
    }

    // Watch for ORCID ID changes and trigger lookup
    $effect(() => {
        if (shouldLookup) {
            lookupOrcid();
        }
    });

    // Clear results when input changes
    function handleInput(event: Event) {
        const target = event.target as HTMLInputElement;
        orcidId = target.value;
        foundAuthor = null;
        error = null;
    }
</script>

<div class="space-y-4">
        <!-- ORCID Input -->
        <div>
            <label for="orcid" class="block text-sm font-medium text-gray-700 mb-1">
                ORCID ID
            </label>
            <div class="flex space-x-2">
                <input
                    type="text"
                    id="orcid"
                    value={orcidId}
                    oninput={handleInput}
                    placeholder="0000-0002-0424-2651"
                    class="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 {isValidOrcid ? 'border-green-500' : orcidId.length > 0 ? 'border-red-500' : ''}"
                />
                {#if isLoading}
                    <div class="flex items-center px-3 py-2">
                        <svg class="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                    </div>
                {/if}
            </div>
            {#if orcidId.length > 0 && !isValidOrcid}
                <p class="mt-1 text-sm text-red-600">Please enter a valid ORCID ID (format: 0000-0000-0000-0000)</p>
            {/if}
        </div>

        <!-- Error Message -->
        {#if error}
            <div class="bg-red-50 border border-red-200 rounded-md p-3">
                <p class="text-sm text-red-600">{error}</p>
            </div>
        {/if}

        <!-- Found Author Preview -->
        {#if foundAuthor}
            <div class="bg-green-50 border border-green-200 rounded-md p-3">
                <h4 class="text-sm font-medium text-green-800 mb-2">Author Found:</h4>
                <div class="text-sm text-green-700">
                    <p><strong>Name:</strong> {foundAuthor.first_name} {foundAuthor.last_name}</p>
                    {#if foundAuthor.affiliation}
                        <p><strong>Affiliation:</strong> {foundAuthor.affiliation}</p>
                    {/if}
                    <p class="text-xs text-green-600 mt-2">✓ Automatically added to authors list</p>
                </div>
            </div>
        {/if}

        <!-- Help Text -->
        <div class="text-xs text-gray-600">
            <p>Enter an ORCID ID to automatically fetch and add author information. The author will be added to your metadata entry.</p>
        </div>
    </div> 