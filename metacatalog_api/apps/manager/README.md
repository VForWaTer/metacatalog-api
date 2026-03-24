# sv

Everything you need to build a Svelte project, powered by [`sv`](https://github.com/sveltejs/cli).

## Creating a project

If you're seeing this, you've probably already done this step. Congrats!

```bash
# create a new project in the current directory
npx sv create

# create a new project in my-app
npx sv create my-app
```

## Developing

Once you've created a project and installed dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```bash
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

## Building

To create a production version of your app:

```bash
npm run build
```

You can preview the production build with `npm run preview`.

> To deploy your app, you may need to install an [adapter](https://svelte.dev/docs/kit/adapters) for your target environment.

## Token injection (embedding / iframe)

To pass an API key from a parent app or iframe (e.g. Django with federated login), add the `token` query parameter to the manager URL. The app will validate it, store it in localStorage, and remove it from the address bar.

Example: `https://example.com/manager?token=YOUR_TOKEN`

Use this for iframe `src` or redirects after login. Prefer short-lived or one-time tokens when passing secrets in the URL.
