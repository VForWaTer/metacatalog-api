<script lang="ts">
	import '../app.css';
	
	let { children } = $props();
</script>

<div class="pt-4 bg-gray-100 h-screen w-screen overflow-y-auto">
	{@render children()}
</div>

