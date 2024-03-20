import { defineConfig } from 'vite';
import solidPlugin from 'vite-plugin-solid';
import fs from 'fs';
import path from 'path';
// import devtools from 'solid-devtools/vite'

export default defineConfig({
  base: './',
  plugins: [
    /*
    Uncomment the following line to enable solid-devtools.
    For more info see https://github.com/thetarnav/solid-devtools/tree/main/packages/extension#readme
    */
    // devtools(),
    solidPlugin(),
  ],
  server: {
    // Show to everyone on the network
    host: '0.0.0.0',
    port: 3000,
    cors: {
      origin: "*",
      allowedHeaders: ["Access-Control-Allow-Origin", "Access-Control-Allow-Methods"]
    },
    https: {
      key: fs.readFileSync(path.resolve(__dirname, './server.key')),
      cert: fs.readFileSync(path.resolve(__dirname, './server.crt')),
    }
  },
  build: {
    target: 'esnext',
  },
});
