import { assetUrl, loadConfig, loadIndex, modelKeys } from "./data.js";

const list = document.getElementById("model-list");
const countLabel = document.getElementById("count-label");
const modeLabel = document.getElementById("mode-label");
const searchInput = document.getElementById("search-input");

function modelHref(id) {
  const params = new URLSearchParams(window.location.search);
  const bucket = params.get("bucket");
  const target = new URL("model.html", window.location.href);
  target.searchParams.set("id", id);
  if (bucket) {
    target.searchParams.set("bucket", bucket);
  }
  return target.pathname + target.search;
}

function renderRows(models, config) {
  if (!models.length) {
    list.innerHTML = '<tr><td colspan="4">No models found.</td></tr>';
    return;
  }
  list.innerHTML = models.map((model) => {
    const keys = modelKeys(model.id);
    const metadataUrl = assetUrl(config, keys.metadata);
    return `<tr>
      <td class="id-cell"><a href="${modelHref(model.id)}">${model.id}</a></td>
      <td><a href="${modelHref(model.id)}">${model.name}</a></td>
      <td class="dim-cell">${model.dimensions_label || ""}</td>
      <td>${model.description}<br><a class="small-link" href="${metadataUrl}">metadata</a></td>
    </tr>`;
  }).join("");
}

async function main() {
  const config = await loadConfig();
  modeLabel.textContent = config.mode === "local" ? "Local bucket" : "Remote bucket proxy";
  const index = await loadIndex(config);
  const models = index.models || [];
  countLabel.textContent = `${models.length} model${models.length === 1 ? "" : "s"}`;
  renderRows(models, config);

  searchInput.addEventListener("input", () => {
    const query = searchInput.value.trim().toLowerCase();
    const filtered = models.filter((model) => {
      return `${model.id} ${model.name} ${model.description}`.toLowerCase().includes(query);
    });
    countLabel.textContent = `${filtered.length} of ${models.length} shown`;
    renderRows(filtered, config);
  });
}

main().catch((error) => {
  list.innerHTML = `<tr><td colspan="4">${error.message}</td></tr>`;
  countLabel.textContent = "Index failed";
});
