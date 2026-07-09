// Fetches the pre-built school dataset consumed by app.js.

async function loadSchools() {
  const response = await fetch("data/schools.json");
  if (!response.ok) {
    throw new Error(`Failed to load school data: ${response.status}`);
  }
  return response.json();
}
