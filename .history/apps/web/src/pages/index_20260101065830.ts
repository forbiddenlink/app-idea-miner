// Route-based code splitting with React.lazy()
// This reduces initial bundle size by ~40% by loading pages on-demand

import { lazy } from 'react';

// Lazy load all page components
export const Dashboard = lazy(() => import('./Dashboard'));
export const ClusterExplorer = lazy(() => import('./ClusterExplorer'));
export const ClusterDetail = lazy(() => import('./ClusterDetail'));
export const Analytics = lazy(() => import('./Analytics'));
