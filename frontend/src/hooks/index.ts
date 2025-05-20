import * as useDataHooks from './useDataHooks';
import * as useFusionHooks from './useFusionHooks';
import * as useDiagnosticsHooks from './useDiagnosticsHooks';
import * as useProductHooks from './useProductHooks';
import * as useTaskHooks from './useTaskHooks';
import * as useAuthHooks from './useAuthHooks';

// Export all hooks
export {
  useDataHooks,
  useFusionHooks,
  useDiagnosticsHooks,
  useProductHooks,
  useTaskHooks,
  useAuthHooks
};

// Export individual hooks for convenience
export * from './useDataHooks';
export * from './useFusionHooks';
export * from './useDiagnosticsHooks';
export * from './useProductHooks';
export * from './useTaskHooks';
export * from './useAuthHooks';
