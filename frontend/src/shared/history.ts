export interface HistoryEntry {
  scan_id: string;
  status: string;
  classification?: string;
  date: string;
}

const STORAGE_KEY = 'cybersathi_history';

export function readHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveHistory(entry: HistoryEntry): void {
  try {
    const list = readHistory().filter((i) => i.scan_id !== entry.scan_id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify([entry, ...list].slice(0, 50)));
  } catch {
    // LocalStorage quota handling
  }
}

export function removeHistory(scanId: string): void {
  try {
    const list = readHistory().filter((i) => i.scan_id !== scanId);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  } catch {
    // LocalStorage quota handling
  }
}