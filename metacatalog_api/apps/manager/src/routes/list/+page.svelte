<script lang="ts">
	import { appPath } from '$lib/utils';
	import { goto } from '$app/navigation';
	import { invalidateAll } from '$app/navigation';
	import type { PageData } from './$types';
	import { onMount } from 'svelte';
	import { buildApiUrl } from '$lib/stores/settingsStore';
	
	let { data } = $props<{ data: PageData }>();
	let searchQuery = $state(data.searchQuery);
	let loading = $state(false);
	let searchTimeout: number | null = null;
	let isSearchPending = $state(false);
	let exportFormats = $state<Array<{format: string, display_name: string, path: string, methods: string[]}>>([]);

	// Fetch available export formats
	async function fetchExportFormats() {
		try {
			const response = await fetch(buildApiUrl('/export-formats'));
			if (response.ok) {
				const data = await response.json();
				// Remove duplicates based on format name
				const uniqueFormats = data.export_formats.filter((format: any, index: number, self: any[]) => 
					index === self.findIndex(f => f.format === format.format)
				);
				exportFormats = uniqueFormats;
			}
		} catch (error) {
			console.error('Failed to fetch export formats:', error);
		}
	}

	// Handle dropdown functionality
	onMount(() => {
		// Fetch export formats on component mount
		fetchExportFormats();

		function handleClickOutside(event: MouseEvent) {
			const target = event.target as Element;
			if (!target.closest('.relative.group')) {
				// Close all dropdowns
				document.querySelectorAll('.dropdown-menu').forEach(dropdown => {
					dropdown.classList.add('hidden');
				});
			}
		}

		document.addEventListener('click', handleClickOutside);
		
		return () => {
			document.removeEventListener('click', handleClickOutside);
		};
	});

	function toggleDropdown(event: MouseEvent) {
		event.preventDefault();
		event.stopPropagation();
		
		// Close all other dropdowns first
		document.querySelectorAll('.dropdown-menu').forEach(dropdown => {
			if (dropdown !== (event.target as Element)?.closest('.relative')?.querySelector('.dropdown-menu')) {
				dropdown.classList.add('hidden');
			}
		});
		
		// Toggle current dropdown
		const dropdown = (event.target as Element)?.closest('.relative')?.querySelector('.dropdown-menu');
		dropdown?.classList.toggle('hidden');
	}

	// Debounced search function
	async function performSearch(query: string) {
		loading = true;
		
		try {
			// Update URL without causing page reload to preserve focus
			const url = new URL(window.location.href);
			if (!query.trim()) {
				url.searchParams.delete('search');
			} else {
				url.searchParams.set('search', query);
			}
			
			// Update the URL in the browser history
			window.history.replaceState({}, '', url.toString());
			
			// Invalidate and reload data
			await invalidateAll();
		} finally {
			loading = false;
		}
	}

	// Debounced search with 600ms delay
	function debouncedSearch(query: string) {
		// Clear previous timeout
		if (searchTimeout) {
			clearTimeout(searchTimeout);
		}
		
		// Show pending state
		isSearchPending = true;
		
		// Set new timeout
		searchTimeout = setTimeout(() => {
			isSearchPending = false;
			performSearch(query);
		}, 600);
	}

	// Watch for changes in searchQuery and trigger debounced search
	$effect(() => {
		debouncedSearch(searchQuery);
	});

	// Manual search function (for button click or Enter key)
	async function searchEntries() {
		// Clear any pending debounced search
		if (searchTimeout) {
			clearTimeout(searchTimeout);
		}
		
		// Clear pending state
		isSearchPending = false;
		
		await performSearch(searchQuery);
	}

	function handleKeyPress(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			searchEntries();
		}
	}
</script>

<svelte:head>
	<title>Browse Entries - Metacatalog Manager</title>
</svelte:head>

<div class="max-w-6xl mx-auto px-4 py-8">
	<!-- Back Button -->
	<div class="mb-6">
		<a href={appPath('')} class="inline-flex items-center text-blue-600 hover:text-blue-800">
			<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
			</svg>
			Back to Home
		</a>
	</div>

	<header class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900 mb-4">Browse Entries</h1>
		<p class="text-gray-600">View and search through all metadata entries</p>
	</header>

	<div class="bg-white rounded-lg shadow-md p-6">
		<div class="mb-6">
			<div class="flex gap-4 mb-4">
				<div class="flex-1 relative">
					<input 
						type="text" 
						bind:value={searchQuery}
						placeholder="Search entries... (searches automatically as you type)" 
						onkeypress={handleKeyPress}
						class="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
					{#if loading || isSearchPending}
						<div class="absolute right-3 top-1/2 transform -translate-y-1/2">
							<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
						</div>
					{/if}
				</div>
				<button 
					onclick={searchEntries}
					class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
					disabled={loading}
					title="Search immediately (bypasses debounce)"
				>
					{#if loading}
						<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
						Searching...
					{:else if isSearchPending}
						<div class="animate-pulse rounded-full h-4 w-4 bg-white opacity-70"></div>
						Search Pending
					{:else}
						Search Now
					{/if}
				</button>
			</div>
			{#if loading}
				<div class="text-sm text-gray-500 mb-2">
					Searching...
				</div>
			{:else if isSearchPending}
				<div class="text-sm text-gray-500 mb-2">
					Search will start in a moment...
				</div>
			{/if}
		</div>

		{#if data.entries.length === 0}
			<div class="text-center py-8">
				<p class="text-gray-500">
					{searchQuery ? 'No entries found matching your search.' : 'No entries found.'}
				</p>
			</div>
		{:else}
			<div class="space-y-4">
				{#each data.entries as entry}
					<div class="border border-gray-200 rounded-lg hover:shadow-md transition-shadow hover:border-blue-300 flex">
						<!-- Main content area -->
						<div class="flex-1 p-4">
							<h3 class="text-lg font-semibold text-gray-900 mb-2">{entry.title || 'Untitled Entry'}</h3>
							<p class="text-gray-600 mb-2">{entry.abstract || entry.description || 'No description available'}</p>
							<div class="flex gap-2 text-sm text-gray-500">
								{#if entry.author}
									<span>Author: {entry.author.first_name} {entry.author.last_name}</span>
								{/if}
								{#if entry.lastUpdate}
									<span>•</span>
									<span>Updated: {new Date(entry.lastUpdate).toLocaleDateString()}</span>
								{/if}
								{#if entry.id}
									<span>•</span>
									<span>ID: {entry.id}</span>
								{/if}
							</div>
						</div>
						
						<!-- Action buttons area -->
						<div class="flex flex-col border-l border-gray-200">
							<!-- Export dropdown -->
							<div class="relative group">
								<button 
									class="px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 border-b border-gray-200 flex items-center gap-1"
									onclick={toggleDropdown}
								>
									Export
									<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
									</svg>
								</button>
								<div class="dropdown-menu hidden absolute right-0 top-full bg-white border border-gray-200 rounded-md shadow-lg z-10 min-w-[160px]">
									{#each exportFormats as format}
										<a 
											href={buildApiUrl(`/export/${entry.id}/${format.format}`)}
											class="block px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
											onclick={(e) => e.stopPropagation()}
											target="_blank"
										>
											{format.display_name}
										</a>
									{/each}
									{#if exportFormats.length === 0}
										<div class="px-3 py-2 text-sm text-gray-500">
											Loading...
										</div>
									{/if}
								</div>
							</div>
							
							<!-- Open button (chevron) -->
							<a 
								href={appPath(`datasets/${entry.id}`)}
								class="flex-1 flex items-center justify-center px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-50"
								aria-label="View details"
							>
								<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
								</svg>
							</a>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
