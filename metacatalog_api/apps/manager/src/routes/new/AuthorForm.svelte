<script lang="ts">
    import type { Author, AuthorCreate } from '$lib/models';
    import { metadataEntry, metadataActions } from '$lib/stores/metadataStore';
    import OrcidLookup from '$lib/components/OrcidLookup.svelte';

    // Props
    let { authors } = $props<{ authors: Author[] }>();

    // Local state for collapsible sections
    let orcidSectionOpen = $state(true);
    let addAuthorSectionOpen = $state(false);
    let existingAuthorSectionOpen = $state(true);

    // Local state for new author form
    let newAuthor = $state<AuthorCreate>({
        first_name: '',
        last_name: '',
        is_organisation: false,
        organisation_name: '',
        organisation_abbrev: '',
        affiliation: ''
    });

    // Handle adding new author
    function addNewAuthor() {
        const hasValidData = newAuthor.is_organisation 
            ? (newAuthor.organisation_name || '').trim() || (newAuthor.organisation_abbrev || '').trim()
            : (newAuthor.first_name || '').trim() || (newAuthor.last_name || '').trim();
            
        if (hasValidData) {
            // Check if we already have a main author
            const hasMainAuthor = $metadataEntry.author && 
                ((($metadataEntry.author as AuthorCreate).first_name || '').trim() || 
                 (($metadataEntry.author as AuthorCreate).last_name || '').trim() ||
                 (($metadataEntry.author as AuthorCreate).organisation_name || '').trim() ||
                 (($metadataEntry.author as AuthorCreate).organisation_abbrev || '').trim());
            
            console.log('🔍 Manual author addition - hasMainAuthor:', hasMainAuthor, 'author:', $metadataEntry.author);
            
            if (hasMainAuthor) {
                // Add as co-author
                metadataActions.addCoAuthor({...newAuthor});
            } else {
                // Set as main author
                metadataActions.updateAuthor({...newAuthor});
            }
            
            // Reset form
            newAuthor = {
                first_name: '',
                last_name: '',
                is_organisation: false,
                organisation_name: '',
                organisation_abbrev: '',
                affiliation: ''
            };
        }
    }

    // Handle removing author
    function removeAuthor(index: number) {
        metadataActions.removeCoAuthor(index);
    }

    // Handle removing main author
    function removeMainAuthor() {
        metadataActions.updateAuthor({ first_name: '', last_name: '', is_organisation: false, organisation_name: '', organisation_abbrev: '', affiliation: '' });
    }

    // Handle reordering co-authors
    function moveCoAuthorUp(index: number) {
        if (index > 0) {
            const coAuthors = [...($metadataEntry.coAuthors || [])];
            const temp = coAuthors[index];
            coAuthors[index] = coAuthors[index - 1];
            coAuthors[index - 1] = temp;
            metadataActions.updateCoAuthors(coAuthors);
        }
    }

    function moveCoAuthorDown(index: number) {
        const coAuthors = [...($metadataEntry.coAuthors || [])];
        if (index < coAuthors.length - 1) {
            const temp = coAuthors[index];
            coAuthors[index] = coAuthors[index + 1];
            coAuthors[index + 1] = temp;
            metadataActions.updateCoAuthors(coAuthors);
        }
    }

    // Handle field updates
    function updateOrgName(value: string) {
        newAuthor.organisation_name = value;
    }

    function updateOrgAbbrev(value: string) {
        newAuthor.organisation_abbrev = value;
    }

    function updateAffiliation(value: string) {
        newAuthor.affiliation = value;
    }

    // Handle ORCID lookup result
    function handleOrcidAuthorFound(event: CustomEvent<[AuthorCreate]>) {
        const [author] = event.detail;
        
        // Check if we already have a main author
        const hasMainAuthor = $metadataEntry.author && 
            ((($metadataEntry.author as AuthorCreate).first_name || '').trim() || 
             (($metadataEntry.author as AuthorCreate).last_name || '').trim() ||
             (($metadataEntry.author as AuthorCreate).organisation_name || '').trim() ||
             (($metadataEntry.author as AuthorCreate).organisation_abbrev || '').trim());
        
        console.log('🔍 ORCID author found - hasMainAuthor:', hasMainAuthor, 'author:', $metadataEntry.author);
        
        if (hasMainAuthor) {
            // Add as co-author
            metadataActions.addCoAuthor({...author});
        } else {
            // Set as main author
            metadataActions.updateAuthor({...author});
        }
    }

    // Handle selecting existing author from dropdown
    function handleExistingAuthorSelect(event: Event) {
        const target = event.target as HTMLSelectElement;
        const authorId = parseInt(target.value);
        
        if (authorId) {
            const selectedAuthor = authors.find((a: Author) => a.id === authorId);
            if (selectedAuthor) {
                // Convert Author to AuthorCreate format
                const authorCreate: AuthorCreate = {
                    first_name: selectedAuthor.first_name || '',
                    last_name: selectedAuthor.last_name || '',
                    is_organisation: selectedAuthor.is_organisation || false,
                    organisation_name: selectedAuthor.organisation_name || '',
                    organisation_abbrev: selectedAuthor.organisation_abbrev || '',
                    affiliation: selectedAuthor.affiliation || ''
                };
                
                // Check if we already have a main author (same logic as other functions)
                const hasMainAuthor = $metadataEntry.author && 
                    ((($metadataEntry.author as AuthorCreate).first_name || '').trim() || 
                     (($metadataEntry.author as AuthorCreate).last_name || '').trim() ||
                     (($metadataEntry.author as AuthorCreate).organisation_name || '').trim() ||
                     (($metadataEntry.author as AuthorCreate).organisation_abbrev || '').trim());
                
                console.log('🔍 Existing author selection - hasMainAuthor:', hasMainAuthor, 'author:', $metadataEntry.author);
                
                if (hasMainAuthor) {
                    // Add as co-author
                    metadataActions.addCoAuthor(authorCreate);
                } else {
                    // Set as main author
                    metadataActions.updateAuthor(authorCreate);
                }
                
                // Reset dropdown
                target.value = '';
            }
        }
    }



    // Get all associated authors (main author + co-authors)
    const associatedAuthors = $derived((() => {
        const allAuthors: (Author | AuthorCreate)[] = [];
        
        // Add main author if exists
        if ($metadataEntry.author) {
            const author = $metadataEntry.author as AuthorCreate;
            const hasValidData = author.is_organisation 
                ? (author.organisation_name || '').trim() || (author.organisation_abbrev || '').trim()
                : (author.first_name || '').trim() || (author.last_name || '').trim();
                
            if (hasValidData) {
                allAuthors.push(author);
            }
        }
        
        // Add co-authors
        if ($metadataEntry.coAuthors) {
            allAuthors.push(...($metadataEntry.coAuthors as (Author | AuthorCreate)[]));
        }
        
        return allAuthors;
    })());
</script>

<div class="space-y-6">
    <!-- ORCID Lookup -->
    <div class="bg-gray-50 p-4 rounded-md">
        <button
            type="button"
            onmousedown={() => orcidSectionOpen = !orcidSectionOpen}
            class="flex items-center justify-between w-full text-left"
        >
            <h3 class="text-lg font-medium text-gray-900">ORCID Lookup</h3>
            <svg 
                class="w-5 h-5 text-gray-500 transform transition-transform {orcidSectionOpen ? 'rotate-180' : ''}" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
            >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
        </button>
        
        {#if orcidSectionOpen}
            <div class="mt-4">
                <OrcidLookup on:authorFound={handleOrcidAuthorFound} />
            </div>
        {/if}
    </div>

    <!-- Select Existing Author -->
    <div class="bg-gray-50 p-4 rounded-md">
        <button
            type="button"
            onmousedown={() => existingAuthorSectionOpen = !existingAuthorSectionOpen}
            class="flex items-center justify-between w-full text-left"
        >
            <h3 class="text-lg font-medium text-gray-900">Select Existing Author</h3>
            <svg 
                class="w-5 h-5 text-gray-500 transform transition-transform {existingAuthorSectionOpen ? 'rotate-180' : ''}" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
            >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
        </button>
        
        {#if existingAuthorSectionOpen}
            <div class="mt-4">
                <label for="existing-author" class="block text-sm font-medium text-gray-700 mb-2">
                    Choose from existing authors
                </label>
                <select
                    id="existing-author"
                    onchange={handleExistingAuthorSelect}
                    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                >
                    <option value="">Select an author...</option>
                    {#each authors.filter((author: Author) => !associatedAuthors.some(associated => {
                        // Check by ID first (for existing authors from database)
                        if ('id' in associated && associated.id && associated.id === author.id) {
                            return true;
                        }
                        // Check by name/organization (for newly added authors)
                        if (author.is_organisation) {
                            return (author.organisation_name || '').trim() === (associated.organisation_name || '').trim() &&
                                   (author.organisation_abbrev || '').trim() === (associated.organisation_abbrev || '').trim();
                        } else {
                            return (author.first_name || '').trim() === (associated.first_name || '').trim() &&
                                   (author.last_name || '').trim() === (associated.last_name || '').trim();
                        }
                    })) as author}
                        <option value={author.id}>
                            {#if author.is_organisation}
                                {author.organisation_name || author.first_name || author.last_name}
                                {#if author.organisation_abbrev}
                                    ({author.organisation_abbrev})
                                {/if}
                            {:else}
                                {author.first_name} {author.last_name}
                            {/if}
                            {#if author.affiliation}
                                - {author.affiliation}
                            {/if}
                        </option>
                    {/each}
                </select>
            </div>
        {/if}
    </div>

    <!-- Add New Author Form -->
    <div class="bg-gray-50 p-4 rounded-md">
        <button
            type="button"
            onmousedown={() => addAuthorSectionOpen = !addAuthorSectionOpen}
            class="flex items-center justify-between w-full text-left"
        >
            <h3 class="text-lg font-medium text-gray-900">Add New Author</h3>
            <svg 
                class="w-5 h-5 text-gray-500 transform transition-transform {addAuthorSectionOpen ? 'rotate-180' : ''}" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
            >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
        </button>
        
                {#if addAuthorSectionOpen}
            <div class="mt-4">
                <div class="grid grid-cols-1 sm:grid-cols-6 md:grid-cols-3 lg:grid-cols-6 gap-3 items-end">
            <!-- First Name -->
            <div>
                <label for="first_name" class="block text-xs font-medium text-gray-700 mb-1">
                    First Name
                </label>
                <input
                    type="text"
                    id="first_name"
                    bind:value={newAuthor.first_name}
                    disabled={newAuthor.is_organisation}
                    class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-gray-900 {newAuthor.is_organisation ? 'bg-gray-100 cursor-not-allowed' : ''}"
                    placeholder="First"
                />
            </div>
            
            <!-- Last Name -->
            <div>
                <label for="last_name" class="block text-xs font-medium text-gray-700 mb-1">
                    Last Name
                </label>
                <input
                    type="text"
                    id="last_name"
                    bind:value={newAuthor.last_name}
                    disabled={newAuthor.is_organisation}
                    class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-gray-900 {newAuthor.is_organisation ? 'bg-gray-100 cursor-not-allowed' : ''}"
                    placeholder="Last"
                />
            </div>
            
            <!-- Organisation Toggle -->
            <div class="flex items-center justify-center">
                <input
                    type="checkbox"
                    id="is_organisation"
                    bind:checked={newAuthor.is_organisation}
                    class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label for="is_organisation" class="ml-2 text-xs text-gray-700">
                    Org
                </label>
            </div>

            <!-- Organisation Name -->
            <div>
                <label for="org_name" class="block text-xs font-medium text-gray-700 mb-1">
                    Org Name
                </label>
                <input
                    type="text"
                    id="org_name"
                    bind:value={newAuthor.organisation_name}
                    class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                    placeholder="Organisation name"
                />
            </div>
            
            <!-- Organisation Abbreviation -->
            <div>
                <label for="org_abbrev" class="block text-xs font-medium text-gray-700 mb-1">
                    Org Abbrev
                </label>
                <input
                    type="text"
                    id="org_abbrev"
                    bind:value={newAuthor.organisation_abbrev}
                    class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                    placeholder="NASA"
                />
            </div>
            
            <!-- Affiliation -->
            <div>
                <label for="affiliation" class="block text-xs font-medium text-gray-700 mb-1">
                    Affiliation
                </label>
                <input
                    type="text"
                    id="affiliation"
                    bind:value={newAuthor.affiliation}
                    class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                    placeholder="Institution, dept"
                />
            </div>
            

            
            <!-- Add Button -->
            <div>
                <button
                    type="button"
                    onmousedown={addNewAuthor}
                    class="w-full px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:ring-offset-1"
                >
                    Add
                </button>
            </div>
                </div>
            </div>
        {/if}
    </div>

    <!-- Associated Authors Table -->
    <div>
        <h3 class="text-lg font-medium text-gray-900 mb-4">Associated Authors</h3>
        
        {#if associatedAuthors.length > 0}
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Name
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Type
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Affiliation
                            </th>

                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Role
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Actions
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        {#each associatedAuthors as author, index}
                            {@const authorData = author as AuthorCreate}
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    {#if authorData.is_organisation}
                                        {authorData.organisation_name || authorData.first_name || authorData.last_name}
                                        {#if authorData.organisation_abbrev}
                                            <span class="text-gray-500">({authorData.organisation_abbrev})</span>
                                        {/if}
                                    {:else}
                                        {authorData.first_name} {authorData.last_name}
                                    {/if}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {authorData.is_organisation ? 'Organisation' : 'Person'}
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500 max-w-xs">
                                    <div class="truncate" title={authorData.affiliation || '-'}>
                                        {authorData.affiliation || '-'}
                                    </div>
                                </td>

                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {index === 0 ? 'Main Author' : 'Co-Author'}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    <div class="flex items-center space-x-1">
                                        {#if index > 0}
                                            <!-- Up arrow for co-authors -->
                                            <button
                                                type="button"
                                                onmousedown={() => moveCoAuthorUp(index - 1)}
                                                class="text-gray-400 hover:text-gray-600"
                                                title="Move up"
                                                aria-label="Move up"
                                            >
                                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path>
                                                </svg>
                                            </button>
                                            
                                            <!-- Down arrow for co-authors -->
                                            <button
                                                type="button"
                                                onmousedown={() => moveCoAuthorDown(index - 1)}
                                                class="text-gray-400 hover:text-gray-600"
                                                title="Move down"
                                                aria-label="Move down"
                                            >
                                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                                                </svg>
                                            </button>
                                        {/if}
                                        
                                        <!-- Remove button for all authors -->
                                        <button
                                            type="button"
                                            onmousedown={() => index === 0 ? removeMainAuthor() : removeAuthor(index - 1)}
                                            class="text-red-600 hover:text-red-900"
                                        >
                                            Remove
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        {:else}
            <p class="text-gray-500 italic">No authors associated with this metadata entry.</p>
        {/if}
    </div>

</div> 