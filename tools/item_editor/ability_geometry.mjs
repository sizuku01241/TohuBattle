export const distance2D = (a, b) => Math.hypot(a.x - b.x, a.z - b.z);
export const inCircle = (origin, point, radius) => distance2D(origin, point) <= radius;
export const inCone = (origin, direction, point, radius, angleDegrees) => {
  const dx = point.x - origin.x; const dz = point.z - origin.z; const length = Math.hypot(dx, dz);
  if (length > radius || length === 0) return length === 0;
  return (dx * direction.x + dz * direction.z) / length >= Math.cos((angleDegrees * Math.PI) / 360);
};
export const inLine = (origin, direction, point, length, width) => {
  const dx = point.x - origin.x; const dz = point.z - origin.z;
  return dx * direction.x + dz * direction.z >= 0 && dx * direction.x + dz * direction.z <= length && Math.abs(dx * direction.z - dz * direction.x) <= width;
};
