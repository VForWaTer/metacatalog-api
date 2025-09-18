<script>
	import { appPath, externalPath } from '$lib/utils';
</script>

<svelte:head>
	<title>Metacatalog Manager - Home</title>
</svelte:head>

<div class="max-w-6xl mx-auto px-4 py-8">
	<header class="text-center mb-12">
		<h1 class="text-4xl font-bold text-gray-900 mb-4">Metacatalog Manager</h1>
		<p class="text-xl text-gray-600 max-w-2xl mx-auto">
			A modern interface for managing scientific data metadata
		</p>
	</header>

	<section class="mb-12">
		<h2 class="text-2xl font-semibold text-gray-900 mb-6 text-center">Quick Actions</h2>
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
			<a href={externalPath('/docs')} target="_blank" rel="noopener noreferrer" class="block p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200">
				<div class="text-3xl mb-4">📚</div>
				<h3 class="text-lg font-semibold text-gray-900 mb-2">API Documentation</h3>
				<p class="text-gray-600">Explore the complete API documentation with interactive examples.</p>
			</a>
			
			<a href={appPath('list')} class="block p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200">
				<div class="text-3xl mb-4">📋</div>
				<h3 class="text-lg font-semibold text-gray-900 mb-2">Browse Entries</h3>
				<p class="text-gray-600">View and search through all metadata entries.</p>
			</a>
			
			<a href={appPath('new')} class="block p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200">
				<div class="text-3xl mb-4">➕</div>
				<h3 class="text-lg font-semibold text-gray-900 mb-2">Create Entry</h3>
				<p class="text-gray-600">Add new metadata entries with a guided form.</p>
			</a>
			
			<a href={externalPath('/explorer')} class="block p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200">
				<div class="text-3xl mb-4">🔍</div>
				<h3 class="text-lg font-semibold text-gray-900 mb-2">Classic Explorer</h3>
				<p class="text-gray-600">Access the traditional HTML-based explorer interface.</p>
			</a>
		</div>
	</section>

	<section>
		<h2 class="text-2xl font-semibold text-gray-900 mb-6 text-center">Features</h2>
		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			<div class="p-6 bg-gray-50 rounded-lg border-l-4 border-blue-500">
				<h3 class="text-lg font-semibold text-gray-900 mb-2">📊 Rich Metadata</h3>
				<p class="text-gray-600">Comprehensive metadata support including authors, variables, and licenses.</p>
			</div>
			<div class="p-6 bg-gray-50 rounded-lg border-l-4 border-blue-500">
				<h3 class="text-lg font-semibold text-gray-900 mb-2">🌍 Spatial Support</h3>
				<p class="text-gray-600">Built-in support for geographic data with PostGIS integration.</p>
			</div>
			<div class="p-6 bg-gray-50 rounded-lg border-l-4 border-blue-500">
				<h3 class="text-lg font-semibold text-gray-900 mb-2">🔍 Advanced Search</h3>
				<p class="text-gray-600">Full-text search capabilities with filtering options.</p>
			</div>
			<div class="p-6 bg-gray-50 rounded-lg border-l-4 border-blue-500">
				<h3 class="text-lg font-semibold text-gray-900 mb-2">📁 Group Management</h3>
				<p class="text-gray-600">Organize entries into logical groups and collections.</p>
			</div>
		</div>
	</section>
</div>
