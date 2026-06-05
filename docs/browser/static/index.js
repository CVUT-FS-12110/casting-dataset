import { assetUrl, loadConfig, loadIndex, modelKeys } from "./data.js";

const list = document.getElementById("model-list");
const countLabel = document.getElementById("count-label");
const modeLabel = document.getElementById("mode-label");
const searchInput = document.getElementById("search-input");
const columnCount = 8;

function textValue(value) {
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  if (value && typeof value === "object") {
    return JSON.stringify(value);
  }
  return value ?? "";
}

function escapeHtml(value) {
  return String(textValue(value))
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function modelHref(id) {
  const params = new URLSearchParams(window.location.search);
  const bucket = params.get("bucket");
  const target = new URL("model.html", window.location.href);
  target.searchParams.set("id", id);
  if (bucket) {
    target.searchParams.set("bucket", bucket);
  }
  return `${target.pathname.split("/").pop()}${target.search}`;
}

function renderRows(models, config) {
  if (!models.length) {
    list.innerHTML = `<tr><td colspan="${columnCount}">No models found.</td></tr>`;
    return;
  }
  list.innerHTML = models.map((model) => {
    const keys = modelKeys(model.id);
    const metadataUrl = assetUrl(config, keys.metadata);
    return `<tr>
      <td class="id-cell"><a href="${modelHref(model.id)}">${escapeHtml(model.id)}</a></td>
      <td><a href="${modelHref(model.id)}">${escapeHtml(model.name)}</a></td>
      <td class="category-cell">${escapeHtml(model.category)}</td>
      <td class="material-cell">${escapeHtml(model.material)}</td>
      <td class="date-cell">${escapeHtml(model.created)}</td>
      <td class="date-cell">${escapeHtml(model.last_change)}</td>
      <td class="dim-cell">${escapeHtml(model.dimensions_label)}</td>
      <td>${escapeHtml(model.description)}<br><a class="small-link" href="${metadataUrl}">metadata</a></td>
    </tr>`;
  }).join("");
}

function searchableText(model) {
  return [
    model.id,
    model.name,
    model.description,
    model.category,
    textValue(model.material),
    model.created,
    model.last_change,
    model.dimensions_label
  ].join(" ").toLowerCase();
}

async function main() {
  const config = await loadConfig();
  modeLabel.textContent = config.mode === "local" ? "Local bucket" : "Remote bucket";
  const index = await loadIndex(config);
  const models = index.models || [];
  countLabel.textContent = `${models.length} model${models.length === 1 ? "" : "s"}`;
  renderRows(models, config);

  searchInput.addEventListener("input", () => {
    const query = searchInput.value.trim().toLowerCase();
    const filtered = models.filter((model) => {
      return searchableText(model).includes(query);
    });
    countLabel.textContent = `${filtered.length} of ${models.length} shown`;
    renderRows(filtered, config);
  });
}

main().catch((error) => {
  list.innerHTML = `<tr><td colspan="${columnCount}">${escapeHtml(error.message)}</td></tr>`;
  countLabel.textContent = "Index failed";
});
