export async function loadConfig() {
  const params = new URLSearchParams(window.location.search);
  const explicitBucket = params.get("bucket");
  if (explicitBucket) {
    return { assetBaseUrl: explicitBucket.replace(/\/$/, ""), mode: "remote" };
  }
  if (window.CASTING_DATA_BUCKET_URL) {
    return { assetBaseUrl: window.CASTING_DATA_BUCKET_URL.replace(/\/$/, ""), mode: "remote" };
  }
  try {
    const response = await fetch("/config.json");
    if (response.ok) {
      const config = await response.json();
      return {
        assetBaseUrl: config.assetBaseUrl.replace(/\/$/, ""),
        remoteAssetBaseUrl: config.remoteAssetBaseUrl?.replace(/\/$/, ""),
        mode: config.mode || "local"
      };
    }
  } catch {
    // A static-only deployment can skip /config.json and use the default relative bucket.
  }
  return { assetBaseUrl: "/generated", mode: "local" };
}

export function assetUrl(config, key) {
  return `${config.assetBaseUrl}/${key}`;
}

export async function loadIndex(config) {
  const response = await fetch(assetUrl(config, "index.json"));
  if (!response.ok) {
    throw new Error(`Could not load index.json (${response.status})`);
  }
  return response.json();
}

export function modelKeys(id) {
  return {
    metadata: `metadata/${id}.json`,
    mesh: `mesh/${id}.glb`,
    step: `step/${id}.step`,
    sectionX: `sections/${id}-x.png`,
    sectionY: `sections/${id}-y.png`,
    sectionZ: `sections/${id}-z.png`
  };
}
