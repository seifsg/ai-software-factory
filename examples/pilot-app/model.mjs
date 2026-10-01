export function normalizeTitle(value) {
  return value;
}

export function readTasks(storage) {
  try {
    const items = JSON.parse(storage.getItem('task-notes') || '[]');
    return Array.isArray(items) ? items.filter(item => typeof item === 'string') : [];
  } catch {
    return [];
  }
}
