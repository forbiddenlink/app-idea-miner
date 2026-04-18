import "@testing-library/jest-dom";

// Node 22+ ships a native localStorage that shadows jsdom's implementation
// but lacks methods like .clear(). Provide a spec-compliant mock.
const store = new Map<string, string>();

const localStorageMock: Storage = {
  getItem: (key: string) => store.get(key) ?? null,
  setItem: (key: string, value: string) => {
    store.set(key, String(value));
  },
  removeItem: (key: string) => {
    store.delete(key);
  },
  clear: () => {
    store.clear();
  },
  get length() {
    return store.size;
  },
  key: (index: number) => [...store.keys()][index] ?? null,
};

Object.defineProperty(globalThis, "localStorage", { value: localStorageMock });
