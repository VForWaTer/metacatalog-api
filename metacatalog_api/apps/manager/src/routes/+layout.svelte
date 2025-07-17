<script lang="ts">
	import '../app.css';
	import type { LayoutData } from './$types';
	
	let { children, data } = $props<{ children: any; data: LayoutData }>();
</script>

<div class="pt-4 bg-gray-100 h-screen w-screen overflow-y-auto">
	{@render children({ data })}
</div>

