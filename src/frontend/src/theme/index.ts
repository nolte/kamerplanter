// The theme objects are NOT re-exported here. Their consumers import them from
// `@/theme/theme` directly, and a barrel that also offers them gives the same
// value two import paths — which is how half of them ended up reachable only
// through the one nobody used.
export { ThemeContextProvider, useThemeMode } from './ThemeContext';
