export function isInteger(value) { return Number.isInteger(value); }
export function required(value, name) { if (value === undefined || value === null || value === "") throw new Error(`${name} is required`); return value; }
