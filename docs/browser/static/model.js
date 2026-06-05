import { assetUrl, loadConfig, loadIndex, modelKeys } from "./data.js";

const params = new URLSearchParams(window.location.search);
const pathId = window.location.pathname.split("/").filter(Boolean).pop();
const id = params.get("id") || (pathId === "model.html" ? "" : pathId);
const fields = {
  idLabel: document.getElementById("model-id-label"),
  id: document.getElementById("model-id"),
  name: document.getElementById("model-name"),
  description: document.getElementById("model-description"),
  metadata: document.getElementById("metadata-list"),
  stepLink: document.getElementById("step-link"),
  meshLink: document.getElementById("mesh-link"),
  metadataLink: document.getElementById("metadata-link"),
  dimX: document.getElementById("dim-x"),
  dimY: document.getElementById("dim-y"),
  dimZ: document.getElementById("dim-z"),
  sectionX: document.getElementById("section-x"),
  sectionY: document.getElementById("section-y"),
  sectionZ: document.getElementById("section-z"),
  status: document.getElementById("viewer-status")
};

function setStatus(message) {
  fields.status.textContent = message;
}

function displayValue(value) {
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  if (value && typeof value === "object") {
    return JSON.stringify(value);
  }
  return value ?? "";
}

function escapeHtml(value) {
  return String(displayValue(value))
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderMetadata(metadata) {
  fields.metadata.innerHTML = Object.entries(metadata).filter(([key]) => {
    return key !== "dimensions_label";
  }).map(([key, value]) => {
    const label = key.replaceAll("_", " ");
    return `<dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd>`;
  }).join("");
}

function renderDimensions(summary, metadata) {
  const dimensions = metadata.dimensions_mm || summary.dimensions_mm;
  if (!dimensions) {
    return;
  }
  fields.dimX.textContent = `${dimensions.x.toFixed(1)} mm`;
  fields.dimY.textContent = `${dimensions.y.toFixed(1)} mm`;
  fields.dimZ.textContent = `${dimensions.z.toFixed(1)} mm`;
}

function fitCamera(camera, controls, object) {
  const box = new THREE.Box3().setFromObject(object);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z) || 1;
  const distance = maxDim / (2 * Math.tan((camera.fov * Math.PI) / 360));

  camera.position.set(center.x + distance, center.y - distance * 1.25, center.z + distance * 0.8);
  camera.near = Math.max(maxDim / 1000, 0.1);
  camera.far = Math.max(maxDim * 20, 1000);
  camera.updateProjectionMatrix();
  controls.target.copy(center);
  controls.update();
}

async function loadViewer(meshUrl) {
  const viewer = document.getElementById("viewer");
  if (!window.WebGLRenderingContext) {
    setStatus("WebGL is not available in this browser.");
    return;
  }

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf7f9fb);

  const camera = new THREE.PerspectiveCamera(45, viewer.clientWidth / viewer.clientHeight, 0.1, 100000);
  camera.up.set(0, 0, 1);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  renderer.setSize(viewer.clientWidth, viewer.clientHeight);
  viewer.appendChild(renderer.domElement);

  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;

  scene.add(new THREE.AmbientLight(0xffffff, 1.0));
  scene.add(new THREE.HemisphereLight(0xffffff, 0xa7b0ba, 1.2));
  const keyLight = new THREE.DirectionalLight(0xffffff, 1.8);
  keyLight.position.set(1, -1, 2);
  scene.add(keyLight);

  setStatus("Loading model...");
  const loader = new THREE.GLTFLoader();
  const gltf = await new Promise((resolve, reject) => {
    loader.load(meshUrl, resolve, undefined, reject);
  });
  const group = gltf.scene;
  group.traverse((object) => {
    if (!object.isMesh) {
      return;
    }
    object.material = new THREE.MeshBasicMaterial({
      color: 0xd7dee8,
      side: THREE.DoubleSide,
      polygonOffset: true,
      polygonOffsetFactor: 2,
      polygonOffsetUnits: 2
    });
    const edges = new THREE.LineSegments(
      new THREE.EdgesGeometry(object.geometry, 10),
      new THREE.LineBasicMaterial({
        color: 0x05070a,
        transparent: false,
        depthTest: false
      })
    );
    edges.renderOrder = 10;
    object.add(edges);

    const wireframe = new THREE.LineSegments(
      new THREE.WireframeGeometry(object.geometry),
      new THREE.LineBasicMaterial({
        color: 0x0f1720,
        transparent: true,
        opacity: 0.16,
        depthTest: false
      })
    );
    wireframe.renderOrder = 9;
    object.add(wireframe);
  });
  scene.add(group);
  fitCamera(camera, controls, group);
  fields.status.remove();

  function resize() {
    const width = viewer.clientWidth;
    const height = viewer.clientHeight;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  }
  window.addEventListener("resize", resize);

  function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }
  animate();
}

async function main() {
  const config = await loadConfig();
  const index = await loadIndex(config);
  const summary = (index.models || []).find((model) => model.id === id);
  if (!summary) {
    throw new Error(`Model ${id} was not found in index.json`);
  }

  const keys = modelKeys(id);
  const metadataUrl = assetUrl(config, keys.metadata);
  const metadataResponse = await fetch(metadataUrl);
  if (!metadataResponse.ok) {
    throw new Error(`Could not load metadata for ${id}`);
  }
  const metadata = await metadataResponse.json();
  const meshUrl = assetUrl(config, keys.mesh);

  document.title = `${id} ${summary.name}`;
  fields.idLabel.textContent = id;
  fields.id.textContent = id;
  fields.name.textContent = summary.name;
  fields.description.textContent = summary.description;
  fields.stepLink.href = assetUrl(config, keys.step);
  fields.meshLink.href = meshUrl;
  fields.metadataLink.href = metadataUrl;
  fields.sectionX.src = assetUrl(config, keys.sectionX);
  fields.sectionY.src = assetUrl(config, keys.sectionY);
  fields.sectionZ.src = assetUrl(config, keys.sectionZ);
  renderDimensions(summary, metadata);
  renderMetadata(metadata);
  await loadViewer(meshUrl);
}

main().catch((error) => {
  fields.name.textContent = "Model failed to load";
  fields.description.textContent = error.message;
  setStatus(error.message);
});
