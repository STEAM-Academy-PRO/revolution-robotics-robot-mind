import { defineConfig } from 'vite';
import solidPlugin from 'vite-plugin-solid';
import { execSync } from 'child_process';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  base: './',
  plugins: [
    /*
    Uncomment the following line to enable solid-devtools.
    For more info see https://github.com/thetarnav/solid-devtools/tree/main/packages/extension#readme
    */
    // devtools(),
    solidPlugin(),

    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'RR Remote',
        short_name: 'RRRemote',
        start_url: '.',
        display: 'standalone',
        background_color: '#000',
        theme_color: '#000',
        icons: [
          {
            src: 'icon-192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'icon-512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      },
      workbox: {
        cleanupOutdatedCaches: true,
        navigateFallback: 'index.html',
        globPatterns: ['**/*.{js,css,html,png,svg,woff2}'],
        // Increase default 2 MiB limit to allow our bundle to be precached
        maximumFileSizeToCacheInBytes: 10 * 1024 * 1024,
      }
    }),

    {
      name: 'copy-to-pi-firmware-static',
      closeBundle() {
        // Copy all files from dist to ../pi-firmware/static
        execSync('cp -r dist/* ../pi-firmware/static/', { stdio: 'inherit' });
      }
    }
  ],
  server: {
    // Show to everyone on the network
    host: '0.0.0.0',
    port: 3000,
    cors: {
      origin: "*",
      allowedHeaders: ["Access-Control-Allow-Origin", "Access-Control-Allow-Methods"]
    }
  },
  build: {
    target: 'esnext',
  },
});
