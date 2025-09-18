<script lang="ts">
	import { appPath } from '$lib/utils';
	import { goto } from '$app/navigation';
	import type { PageData } from './$types';
	
	let { data } = $props<{ data: PageData }>();
	let searchQuery = $state(data.searchQuery);
	let loading = $state(false);

	async function searchEntries() {
		if (!searchQuery.trim()) {
			await goto('?');
			return;
		}

		await goto(`?search=${encodeURIComponent(searchQuery)}`);
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
				<input 
					type="text" 
					bind:value={searchQuery}
					placeholder="Search entries..." 
					onkeypress={handleKeyPress}
					class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
				/>
				<button 
					onclick={searchEntries}
					class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
					disabled={loading}
				>
					{loading ? 'Searching...' : 'Search'}
				</button>
			</div>
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
					<div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
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
				{/each}
			</div>
		{/if}
	</div>
</div>
