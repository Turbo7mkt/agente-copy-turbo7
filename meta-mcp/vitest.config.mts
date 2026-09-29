import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["tests/**/*.test.ts"],
    // Nenhum teste chama a Meta de verdade: o fetch é substituído pela Meta simulada.
    env: { META_ACCESS_TOKEN: "token-de-teste", META_API_VERSION: "v25.0" },
    restoreMocks: true,
    unstubGlobals: true,
  },
});
