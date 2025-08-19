export const FEATURES = {
  ANALYTICS: (import.meta.env.VITE_ENABLE_ANALYTICS ?? 'false') === 'true',
  UNIFIED_GOV: (import.meta.env.VITE_ENABLE_UNIFIED_GOV ?? 'false') === 'true',
};
