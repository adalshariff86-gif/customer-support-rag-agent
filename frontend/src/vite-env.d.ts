/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_FASTAPI_BACKEND_URL: string;
    readonly VITE_FASTAPI_API_KEY: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}
