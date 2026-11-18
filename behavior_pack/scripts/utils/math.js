export function distance2D(a, b) { const dx = a.x - b.x; const dz = a.z - b.z; return Math.sqrt(dx * dx + dz * dz); }
export function distance3D(a, b) { const dx = a.x - b.x; const dy = a.y - b.y; const dz = a.z - b.z; return Math.sqrt(dx * dx + dy * dy + dz * dz); }
export function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
