// Keeps a speaker's recordings on their own device (IndexedDB) when the site has no server,
// so a refresh or a closed tab doesn't lose them. Falls back to memory if storage is blocked.

const DB = "ug-takes";
const STORE = "takes";
const memory = new Map<string, Blob>();

function open(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

const key = (speaker: string, clip: string) => `${speaker}/${clip}`;

export async function putTake(speaker: string, clip: string, wav: Blob): Promise<void> {
  memory.set(key(speaker, clip), wav);
  try {
    const db = await open();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).put(wav, key(speaker, clip));
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch {
    /* kept in memory only */
  }
}

export async function listTakes(speaker: string): Promise<Map<string, Blob>> {
  const out = new Map<string, Blob>();
  const prefix = speaker + "/";
  try {
    const db = await open();
    await new Promise<void>((resolve, reject) => {
      const req = db.transaction(STORE).objectStore(STORE).openCursor();
      req.onsuccess = () => {
        const c = req.result;
        if (!c) return resolve();
        const k = String(c.key);
        if (k.startsWith(prefix)) out.set(k.slice(prefix.length), c.value as Blob);
        c.continue();
      };
      req.onerror = () => reject(req.error);
    });
  } catch {
    /* storage blocked: use memory below */
  }
  for (const [k, v] of memory) if (k.startsWith(prefix)) out.set(k.slice(prefix.length), v);
  return out;
}
