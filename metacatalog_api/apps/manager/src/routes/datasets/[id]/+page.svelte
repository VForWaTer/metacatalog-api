<script lang="ts">
	import { appPath } from '$lib/utils';
	import { buildApiUrl } from '$lib/stores/settingsStore';
	import type { PageData } from './$types';
	import LocationMap from './LocationMap.svelte';
	import ExportDropdown from '$lib/components/ExportDropdown.svelte';
	
	let { data } = $props<{ data: PageData }>();
	
	// Helper function to format dates
	function formatDate(dateString: string): string {
		if (!dateString) return 'Not specified';
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
	
	// Helper function to format location
	function formatLocation(location: any): string {
		if (!location) return 'Not specified';
		if (location.coordinates && location.coordinates.length === 2) {
			return `${location.coordinates[1].toFixed(6)}, ${location.coordinates[0].toFixed(6)}`;
		}
		return 'Location data available';
	}
</script>

<svelte:head>
	<title>Dataset {data.datasetId} - Metacatalog Manager</title>
</svelte:head>

<div class="max-w-6xl mx-auto px-4 py-8">
	<!-- Back Button -->
	<div class="mb-6">
		<a href={appPath('list')} class="inline-flex items-center text-blue-600 hover:text-blue-800">
			<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
			</svg>
			Back to Entries
		</a>
	</div>

	{#if data.dataset}
		<!-- Header Section -->
		<header class="mb-8">
			<div class="flex justify-between items-start">
				<div>
					<h1 class="text-3xl font-bold text-gray-900 mb-2">{data.dataset.title || 'Untitled Dataset'}</h1>
					<div class="flex items-center gap-4 text-sm text-gray-600">
						<span>ID: {data.dataset.id}</span>
						<span>•</span>
						<span>UUID: {data.dataset.uuid}</span>
						{#if data.dataset.version}
							<span>•</span>
							<span>Version: {data.dataset.version}</span>
						{/if}
					</div>
				</div>
				<div class="flex gap-2">
					<ExportDropdown 
						entryId={data.dataset.id} 
						buttonClass="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm flex items-center gap-1"
					/>
				</div>
			</div>
		</header>
	{:else}
		<header class="mb-8">
			<h1 class="text-3xl font-bold text-gray-900 mb-4">Dataset Details</h1>
			<p class="text-gray-600">Dataset ID: {data.datasetId}</p>
		</header>
	{/if}

	{#if data.notFound}
		<div class="bg-white rounded-lg shadow-md p-6">
			<div class="text-center py-8">
				<div class="text-red-500 mb-4">
					<svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
					</svg>
				</div>
				<h2 class="text-xl font-semibold text-gray-900 mb-2">Dataset Not Found</h2>
				<p class="text-gray-600 mb-4">
					The dataset with ID <code class="bg-gray-100 px-2 py-1 rounded">{data.datasetId}</code> could not be found.
				</p>
				{#if data.error}
					<div class="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
						<p class="text-red-800 text-sm">
							<strong>Error:</strong> {data.error}
						</p>
					</div>
				{/if}
				<a href={appPath('list')} class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
					<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
					</svg>
					Browse All Entries
				</a>
			</div>
		</div>
	{:else if data.dataset}
		<!-- Main Content Grid -->
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
			<!-- Left Column - Main Information -->
			<div class="lg:col-span-2 space-y-6">
				<!-- Abstract -->
				<div class="bg-white rounded-lg shadow-md p-6">
					<h2 class="text-xl font-semibold text-gray-900 mb-4">Abstract</h2>
					<p class="text-gray-700 leading-relaxed">{data.dataset.abstract || 'No abstract provided'}</p>
				</div>

				<!-- Variable Information -->
				{#if data.dataset.variable}
					<div class="bg-white rounded-lg shadow-md p-6">
						<h2 class="text-xl font-semibold text-gray-900 mb-4">Variable Information</h2>
						<div class="space-y-3">
							<div>
								<span class="font-medium text-gray-900">Name:</span>
								<span class="ml-2 text-gray-700">{data.dataset.variable.name}</span>
							</div>
							<div>
								<span class="font-medium text-gray-900">Symbol:</span>
								<span class="ml-2 text-gray-700">{data.dataset.variable.symbol}</span>
							</div>
							{#if data.dataset.variable.unit}
								<div>
									<span class="font-medium text-gray-900">Unit:</span>
									<span class="ml-2 text-gray-700">{data.dataset.variable.unit.name} ({data.dataset.variable.unit.symbol})</span>
								</div>
							{/if}
							{#if data.dataset.variable.column_names && data.dataset.variable.column_names.length > 0}
								<div>
									<span class="font-medium text-gray-900">Column Names:</span>
									<span class="ml-2 text-gray-700">{data.dataset.variable.column_names.join(', ')}</span>
								</div>
							{/if}
							{#if data.dataset.variable.keyword}
								<div>
									<span class="font-medium text-gray-900">Keyword:</span>
									<span class="ml-2 text-gray-700">{data.dataset.variable.keyword.full_path}</span>
								</div>
								{#if data.dataset.variable.keyword.thesaurus}
									<div>
										<span class="font-medium text-gray-900">Thesaurus:</span>
										<span class="ml-2 text-gray-700">{data.dataset.variable.keyword.thesaurus.title} ({data.dataset.variable.keyword.thesaurus.organisation})</span>
									</div>
								{/if}
							{/if}
						</div>
					</div>
				{/if}

				<!-- Author Information -->
				{#if data.dataset.author}
					<div class="bg-white rounded-lg shadow-md p-6">
						<h2 class="text-xl font-semibold text-gray-900 mb-4">Author</h2>
						<div class="space-y-3">
							<div>
								<span class="font-medium text-gray-900">Name:</span>
								<span class="ml-2 text-gray-700">
									{#if data.dataset.author.is_organisation}
										{data.dataset.author.organisation_name || 'Organisation'}
										{#if data.dataset.author.organisation_abbrev}
											({data.dataset.author.organisation_abbrev})
										{/if}
									{:else}
										{data.dataset.author.first_name} {data.dataset.author.last_name}
									{/if}
								</span>
							</div>
							{#if data.dataset.author.affiliation}
								<div>
									<span class="font-medium text-gray-900">Affiliation:</span>
									<span class="ml-2 text-gray-700">{data.dataset.author.affiliation}</span>
								</div>
							{/if}
						</div>
					</div>
				{/if}

				<!-- Co-Authors -->
				{#if data.dataset.coAuthors && data.dataset.coAuthors.length > 0}
					<div class="bg-white rounded-lg shadow-md p-6">
						<h2 class="text-xl font-semibold text-gray-900 mb-4">Co-Authors</h2>
						<div class="space-y-3">
							{#each data.dataset.coAuthors as coAuthor}
								<div class="border-l-4 border-blue-200 pl-4">
									<div>
										<span class="font-medium text-gray-900">Name:</span>
										<span class="ml-2 text-gray-700">
											{#if coAuthor.is_organisation}
												{coAuthor.organisation_name || 'Organisation'}
												{#if coAuthor.organisation_abbrev}
													({coAuthor.organisation_abbrev})
												{/if}
											{:else}
												{coAuthor.first_name} {coAuthor.last_name}
											{/if}
										</span>
									</div>
									{#if coAuthor.affiliation}
										<div>
											<span class="font-medium text-gray-900">Affiliation:</span>
											<span class="ml-2 text-gray-700">{coAuthor.affiliation}</span>
										</div>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Keywords -->
				{#if data.dataset.keywords && data.dataset.keywords.length > 0}
					<div class="bg-white rounded-lg shadow-md p-6">
						<h2 class="text-xl font-semibold text-gray-900 mb-4">Keywords</h2>
						<div class="flex flex-wrap gap-2">
							{#each data.dataset.keywords as keyword}
								<div class="flex flex-col">
									<span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
										{keyword.value}
									</span>
									{#if keyword.thesaurus}
										<span class="text-xs text-gray-500 mt-1 text-center">
											{keyword.thesaurus.name}
										</span>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Details -->
				{#if data.dataset.details && data.dataset.details.length > 0}
					<div class="bg-white rounded-lg shadow-md p-6">
						<h2 class="text-xl font-semibold text-gray-900 mb-4">Additional Details</h2>
						<div class="space-y-3">
							{#each data.dataset.details as detail}
								<div class="border-l-4 border-gray-200 pl-4">
									<div class="font-medium text-gray-900">{detail.key}</div>
									<div class="text-gray-700">
										{#if detail.raw_value && detail.raw_value.__literal__ !== undefined}
											{detail.raw_value.__literal__}
										{:else if detail.raw_value}
											{JSON.stringify(detail.raw_value)}
										{:else}
											No value
										{/if}
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}

			</div>

			<!-- Right Column - Metadata and Actions -->
			<div class="space-y-6">
				<!-- Location Map -->
				{#if data.dataset.location || (data.dataset.datasource && data.dataset.datasource.spatial_scale && data.dataset.datasource.spatial_scale.extent)}
					<div class="bg-white rounded-lg shadow-md p-6">
						<h2 class="text-xl font-semibold text-gray-900 mb-4">Location</h2>
						<LocationMap 
							location={data.dataset.location}
							spatialExtent={data.dataset.datasource?.spatial_scale?.extent}
						/>
					</div>
				{/if}

				<!-- License Information -->
				{#if data.dataset.license}
					<div class="bg-white rounded-lg shadow-md p-6">
						<h2 class="text-xl font-semibold text-gray-900 mb-4">License</h2>
						<div class="space-y-3">
							<div>
								<span class="font-medium text-gray-900">Title:</span>
								<span class="ml-2 text-gray-700">{data.dataset.license.title}</span>
							</div>
							<div>
								<span class="font-medium text-gray-900">Short Title:</span>
								<span class="ml-2 text-gray-700">{data.dataset.license.short_title}</span>
							</div>
							{#if data.dataset.license.link}
								<div>
									<a href={data.dataset.license.link} target="_blank" class="text-blue-600 hover:text-blue-800">
										View License Text
									</a>
								</div>
							{/if}
						</div>
					</div>
				{/if}

				<!-- Dates -->
				<div class="bg-white rounded-lg shadow-md p-6">
					<h2 class="text-xl font-semibold text-gray-900 mb-4">Dates</h2>
					<div class="space-y-3">
						<div>
							<span class="font-medium text-gray-900">Publication:</span>
							<span class="ml-2 text-gray-700">{formatDate(data.dataset.publication)}</span>
						</div>
						<div>
							<span class="font-medium text-gray-900">Last Update:</span>
							<span class="ml-2 text-gray-700">{formatDate(data.dataset.lastUpdate)}</span>
						</div>
						{#if data.dataset.embargo && data.dataset.embargo_end}
							<div>
								<span class="font-medium text-gray-900">Embargo End:</span>
								<span class="ml-2 text-gray-700">{formatDate(data.dataset.embargo_end)}</span>
							</div>
						{/if}
					</div>
				</div>

				<!-- Data Source -->
				{#if data.dataset.datasource}
					<div class="bg-white rounded-lg shadow-md p-6">
						<h2 class="text-xl font-semibold text-gray-900 mb-4">Data Source</h2>
						<div class="space-y-3">
							<div>
								<span class="font-medium text-gray-900">Type:</span>
								<span class="ml-2 text-gray-700">{data.dataset.datasource.type?.title || 'Unknown'}</span>
							</div>
							{#if data.dataset.datasource.path}
								<div>
									<span class="font-medium text-gray-900">Path:</span>
									<div class="ml-2 text-gray-700 font-mono text-sm break-all" title={data.dataset.datasource.path}>
										{data.dataset.datasource.path.length > 60 ? data.dataset.datasource.path.substring(0, 60) + '...' : data.dataset.datasource.path}
									</div>
								</div>
							{/if}
							{#if data.dataset.datasource.encoding}
								<div>
									<span class="font-medium text-gray-900">Encoding:</span>
									<span class="ml-2 text-gray-700">{data.dataset.datasource.encoding}</span>
								</div>
							{/if}
							{#if data.dataset.datasource.temporal_scale}
								<div>
									<span class="font-medium text-gray-900">Temporal Scale:</span>
									<div class="ml-2 text-gray-700 text-sm">
										<div>Resolution: {data.dataset.datasource.temporal_scale.resolution}</div>
										<div>Period: {formatDate(data.dataset.datasource.temporal_scale.observation_start)} - {formatDate(data.dataset.datasource.temporal_scale.observation_end)}</div>
									</div>
								</div>
							{/if}
							{#if data.dataset.datasource.spatial_scale}
								<div>
									<span class="font-medium text-gray-900">Spatial Scale:</span>
									<div class="ml-2 text-gray-700 text-sm">
										<div>Resolution: {data.dataset.datasource.spatial_scale.resolution}m</div>
										<div>Support: {data.dataset.datasource.spatial_scale.support}</div>
									</div>
								</div>
							{/if}
						</div>
					</div>
				{/if}

				<!-- Additional Information -->
				<div class="bg-white rounded-lg shadow-md p-6">
					<h2 class="text-xl font-semibold text-gray-900 mb-4">Additional Information</h2>
					<div class="space-y-3">
						{#if data.dataset.external_id}
							<div>
								<span class="font-medium text-gray-900">External ID:</span>
								<span class="ml-2 text-gray-700">{data.dataset.external_id}</span>
							</div>
						{/if}
						<div>
							<span class="font-medium text-gray-900">Embargo:</span>
							<span class="ml-2 text-gray-700">{data.dataset.embargo ? 'Yes' : 'No'}</span>
						</div>
						<div>
							<span class="font-medium text-gray-900">Is Partial:</span>
							<span class="ml-2 text-gray-700">{data.dataset.is_partial ? 'Yes' : 'No'}</span>
						</div>
						{#if data.dataset.comment}
							<div>
								<span class="font-medium text-gray-900">Comment:</span>
								<span class="ml-2 text-gray-700">{data.dataset.comment}</span>
							</div>
						{/if}
						{#if data.dataset.citation}
							<div>
								<span class="font-medium text-gray-900">Citation:</span>
								<span class="ml-2 text-gray-700">{data.dataset.citation}</span>
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>
	{:else}
		<div class="bg-white rounded-lg shadow-md p-6">
			<div class="text-center py-8">
				<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
				<p class="text-gray-600">Loading dataset...</p>
			</div>
		</div>
	{/if}
</div>
