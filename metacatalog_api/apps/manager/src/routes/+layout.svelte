<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import type { LayoutData } from './$types';
	import TokenModal from '$lib/components/TokenModal.svelte';
	import {
		apiKey,
		tokenModalOpen,
		closeTokenModal,
		openTokenModal,
		hasStoredToken,
		syncApiKeyFromStorage,
		storeAdminToken,
		validateApiKey
	} from '$lib/stores/apiKeyStore';
	import { getBackendUrlFromStore } from '$lib/stores/settingsStore';

	let { children, data } = $props<{ children: any; data: LayoutData }>();

	onMount(() => {
		if (typeof window === 'undefined') return;
		const params = new URLSearchParams(window.location.search);
		const tokenFromUrl = params.get('token');
		if (tokenFromUrl !== null && tokenFromUrl.trim() !== '') {
			const backendUrl = getBackendUrlFromStore();
			validateApiKey(tokenFromUrl.trim(), backendUrl).then((valid) => {
				if (valid) {
					storeAdminToken(tokenFromUrl.trim());
					apiKey.set(tokenFromUrl.trim());
				}
			}).finally(() => {
				params.delete('token');
				const search = params.toString();
				const path = window.location.pathname + (search ? '?' + search : '');
				goto(path, { replaceState: true });
			});
		} else {
			syncApiKeyFromStorage();
		}
	});
</script>

<div class="pt-4 bg-gray-100 h-screen w-screen overflow-y-auto">
	<div class="flex justify-end px-4 pb-2">
		<button
			type="button"
			onclick={openTokenModal}
			class="text-sm text-blue-600 hover:text-blue-800 focus:outline-none"
		>
			{hasStoredToken() ? 'API key' : 'Set API key'}
		</button>
	</div>
	{@render children({ data })}
	<TokenModal isOpen={$tokenModalOpen} onClose={closeTokenModal} />
</div>

