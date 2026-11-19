import { readFile } from "node:fs/promises";
import { readdir } from "node:fs/promises";
import { join, relative } from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const exec = promisify(execFile);
const root = process.cwd();
const requiredManifests = ["behavior_pack/manifest.json", "resource_pack/manifest.json"];
const failures = [];

for (const manifest of requiredManifests) {
  try {
    const value = JSON.parse(await readFile(join(root, manifest), "utf8"));
    if (!value.header?.uuid || !Array.isArray(value.header?.version)) failures.push(`${manifest}: invalid header`);
    if (!Array.isArray(value.modules) || value.modules.length === 0) failures.push(`${manifest}: no modules`);
  } catch (error) { failures.push(`${manifest}: ${error.message}`); }
}

async function walk(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) { const path = join(directory, entry.name); if (entry.isDirectory()) files.push(...await walk(path)); else if (entry.name.endsWith(".js")) files.push(path); }
  return files;
}

for (const file of await walk(join(root, "behavior_pack", "scripts"))) {
  try { await exec(process.execPath, ["--check", file]); } catch (error) { failures.push(`${relative(root, file)}: ${error.stderr || error.message}`); }
}

if (failures.length) { console.error(failures.join("\n")); process.exitCode = 1; }
else console.log("TBR validation passed: manifests and behavior-pack scripts are valid.");
