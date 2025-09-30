<script lang="ts">
	import { appPath } from '$lib/utils';
</script>

<svelte:head>
	<title>Extend MetaCatalog - Documentation</title>
</svelte:head>

<div class="max-w-4xl mx-auto px-4 py-8">
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
		<h1 class="text-3xl font-bold text-gray-900 mb-4">Extend MetaCatalog</h1>
		<p class="text-lg text-gray-600">
			Learn how to create custom export formats and extend MetaCatalog functionality
		</p>
	</header>

	<div class="prose prose-lg max-w-none">
		<section class="mb-8">
			<h2 class="text-2xl font-semibold text-gray-900 mb-4">Overview</h2>
			<p class="text-gray-700 mb-4">
				MetaCatalog is designed to be extensible. You can easily add new export formats, 
				custom routes, and additional functionality by creating your own Python server file 
				similar to the built-in <code class="bg-gray-100 px-2 py-1 rounded">default_server.py</code>.
			</p>
		</section>

		<section class="mb-8">
			<h2 class="text-2xl font-semibold text-gray-900 mb-4">Creating a Custom Server</h2>
			<p class="text-gray-700 mb-4">
				To extend MetaCatalog, create a new Python file that imports and extends the base MetaCatalog functionality:
			</p>
			
			<div class="bg-gray-50 p-6 rounded-lg mb-4">
				<h3 class="font-semibold text-gray-900 mb-3">Step 1: Create your custom server file</h3>
				<p class="text-sm text-gray-600 mb-2">Create a file like <code>my_custom_server.py</code>:</p>
				<ul class="text-sm text-gray-700 space-y-1">
					<li>• Import <code>default_server</code> from <code>metacatalog_api</code></li>
					<li>• Create a custom <code>APIRouter</code></li>
					<li>• Set up Jinja2 templates directory</li>
					<li>• Define your custom export routes</li>
					<li>• Include your router in the main app</li>
				</ul>
			</div>
		</section>

		<section class="mb-8">
			<h2 class="text-2xl font-semibold text-gray-900 mb-4">Export Route Pattern</h2>
			<p class="text-gray-700 mb-4">
				Follow this pattern for your export routes:
			</p>
			
			<div class="bg-gray-50 p-6 rounded-lg mb-4">
				<h3 class="font-semibold text-gray-900 mb-3">Route Structure</h3>
				<ul class="text-sm text-gray-700 space-y-2">
					<li><strong>URL Pattern:</strong> <code>/export/entry_id/format</code></li>
					<li><strong>Method:</strong> GET</li>
					<li><strong>Parameters:</strong> entry_id (int), request (Request)</li>
					<li><strong>Return:</strong> TemplateResponse with your custom template</li>
				</ul>
			</div>
		</section>

		<section class="mb-8">
			<h2 class="text-2xl font-semibold text-gray-900 mb-4">Creating Export Templates</h2>
			<p class="text-gray-700 mb-4">
				Export templates use Jinja2 syntax and have access to the complete entry object:
			</p>
			
			<div class="bg-gray-50 p-6 rounded-lg mb-4">
				<h3 class="font-semibold text-gray-900 mb-3">Template Features</h3>
				<ul class="text-sm text-gray-700 space-y-1">
					<li>• Access entry data with Jinja2 template syntax</li>
					<li>• Use conditionals for optional data</li>
					<li>• Loop through lists and arrays</li>
					<li>• Handle missing data gracefully</li>
					<li>• Support any XML, JSON, or text format</li>
				</ul>
			</div>
		</section>

		<section class="mb-8">
			<h2 class="text-2xl font-semibold text-gray-900 mb-4">Available Entry Data</h2>
			<p class="text-gray-700 mb-4">
				The entry object contains all metadata fields. Here are the main properties you can access:
			</p>
			
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
				<div class="bg-gray-50 p-4 rounded-lg">
					<h3 class="font-semibold text-gray-900 mb-2">Basic Information</h3>
					<ul class="text-sm text-gray-700 space-y-1">
						<li><code>entry.id</code> - Entry ID</li>
						<li><code>entry.uuid</code> - UUID</li>
						<li><code>entry.title</code> - Title</li>
						<li><code>entry.abstract</code> - Abstract</li>
						<li><code>entry.version</code> - Version</li>
						<li><code>entry.publication</code> - Publication date</li>
						<li><code>entry.lastUpdate</code> - Last update</li>
					</ul>
				</div>
				
				<div class="bg-gray-50 p-4 rounded-lg">
					<h3 class="font-semibold text-gray-900 mb-2">Author Information</h3>
					<ul class="text-sm text-gray-700 space-y-1">
						<li><code>entry.author</code> - Main author</li>
						<li><code>entry.coAuthors</code> - Co-authors list</li>
						<li><code>entry.author.first_name</code></li>
						<li><code>entry.author.last_name</code></li>
						<li><code>entry.author.affiliation</code></li>
						<li><code>entry.author.orcid</code></li>
					</ul>
				</div>
				
				<div class="bg-gray-50 p-4 rounded-lg">
					<h3 class="font-semibold text-gray-900 mb-2">Scientific Data</h3>
					<ul class="text-sm text-gray-700 space-y-1">
						<li><code>entry.variable</code> - Variable info</li>
						<li><code>entry.variable.name</code></li>
						<li><code>entry.variable.symbol</code></li>
						<li><code>entry.variable.unit</code></li>
						<li><code>entry.variable.column_names</code></li>
						<li><code>entry.keywords</code> - Keywords list</li>
					</ul>
				</div>
				
				<div class="bg-gray-50 p-4 rounded-lg">
					<h3 class="font-semibold text-gray-900 mb-2">Spatial & Other</h3>
					<ul class="text-sm text-gray-700 space-y-1">
						<li><code>entry.location</code> - Point location</li>
						<li><code>entry.datasource</code> - Data source</li>
						<li><code>entry.license</code> - License info</li>
						<li><code>entry.details</code> - Additional details</li>
						<li><code>entry.embargo</code> - Embargo status</li>
					</ul>
				</div>
			</div>
		</section>

		<section class="mb-8">
			<h2 class="text-2xl font-semibold text-gray-900 mb-4">Running Your Custom Server</h2>
			<p class="text-gray-700 mb-4">
				To run your custom server instead of the default one:
			</p>
			
			<div class="bg-gray-50 p-6 rounded-lg mb-4">
				<div class="text-sm font-mono text-gray-800">
					<p># Instead of running the default server</p>
					<p># uvicorn metacatalog_api.default_server:app</p>
					<br>
					<p># Run your custom server</p>
					<p>uvicorn my_custom_server:app --reload --host 0.0.0.0 --port 8001</p>
				</div>
			</div>
		</section>

		<section class="mb-8">
			<h2 class="text-2xl font-semibold text-gray-900 mb-4">Automatic Discovery</h2>
			<p class="text-gray-700 mb-4">
				The frontend automatically discovers new export formats through the <code class="bg-gray-100 px-2 py-1 rounded">/export-formats</code> endpoint. 
				Your custom export routes will automatically appear in the export dropdown menus across the application.
			</p>
			
			<div class="bg-blue-50 border-l-4 border-blue-400 p-4 mb-4">
				<p class="text-blue-800">
					<strong>Pro Tip:</strong> The first line of your route's docstring becomes the display name in the frontend. 
					Make it descriptive and user-friendly!
				</p>
			</div>
		</section>

		<section class="mb-8">
			<h2 class="text-2xl font-semibold text-gray-900 mb-4">Best Practices</h2>
			<ul class="text-gray-700 space-y-2">
				<li>• Use descriptive docstrings for your export routes (first line becomes the display name)</li>
					<li>• Follow the <code class="bg-gray-100 px-2 py-1 rounded">/export/entry_id/format</code> URL pattern</li>
				<li>• Set appropriate <code class="bg-gray-100 px-2 py-1 rounded">media_type</code> for your exports</li>
				<li>• Handle missing data gracefully with Jinja2 conditionals</li>
				<li>• Test your exports with real data before deploying</li>
				<li>• Consider adding validation for required fields in your format</li>
			</ul>
		</section>

		<section class="mb-8">
			<h2 class="text-2xl font-semibold text-gray-900 mb-4">Example Use Cases</h2>
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div class="bg-gray-50 p-4 rounded-lg">
					<h3 class="font-semibold text-gray-900 mb-2">Research Repositories</h3>
					<ul class="text-sm text-gray-700 space-y-1">
						<li>• DataCite for Zenodo</li>
						<li>• ISO 19115 for geospatial data</li>
						<li>• FGDC for US government data</li>
						<li>• EML for ecological data</li>
					</ul>
				</div>
				
				<div class="bg-gray-50 p-4 rounded-lg">
					<h3 class="font-semibold text-gray-900 mb-2">Custom Formats</h3>
					<ul class="text-sm text-gray-700 space-y-1">
						<li>• Institution-specific schemas</li>
						<li>• Domain-specific formats</li>
						<li>• Legacy system compatibility</li>
						<li>• Integration with other tools</li>
					</ul>
				</div>
			</div>
		</section>

		<section class="mb-8">
			<h2 class="text-2xl font-semibold text-gray-900 mb-4">Need Help?</h2>
			<p class="text-gray-700 mb-4">
				For more advanced customization, check out the MetaCatalog source code and API documentation. 
				The system is built on FastAPI and SQLModel, making it highly extensible.
			</p>
			
			<div class="flex gap-4">
				<a href="/docs" target="_blank" class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
					API Documentation
				</a>
				<a href="https://github.com/your-repo/metacatalog-api" target="_blank" class="inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700">
					Source Code
				</a>
			</div>
		</section>
	</div>
</div>