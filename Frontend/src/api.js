
const BASE = `${process.env.REACT_APP_API_URL}/api`;

// No hardcoded users, projects or tasks — everything comes from DB
// Session storage is only used so newly registered users can log in
// immediately even if backend /users/login endpoint isn't implemented yet

const USERS_KEY = 'tf_users';

export function getStoredUsers() {
  try {
    const raw = sessionStorage.getItem(USERS_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return [];
}

function saveUsers(users) {
  try { sessionStorage.setItem(USERS_KEY, JSON.stringify(users)); } catch {}
}

const toArray = (data, key) => {
  if (!data) return null;
  if (Array.isArray(data)) return data;
  if (key && Array.isArray(data[key])) return data[key];
  if (Array.isArray(data.data)) return data.data;
  return null;
};

async function apiFetch(path, options = {}) {
  try {
    const res = await fetch(`${BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`API [${path}] failed:`, err.message);
    return null;
  }
}

// ── Users ──────────────────────────────────────────────────
export async function fetchUsers() {
  const data = await apiFetch('/users');
  const fromApi = toArray(data, 'users');
  if (fromApi && fromApi.length > 0) return fromApi;
  return getStoredUsers();
}

export async function loginUser(email, password, allUsers) {
  const data = await apiFetch('/users/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (data?.id) return { ...data, password };
  // fallback to session-stored users
  const list = allUsers?.length ? allUsers : getStoredUsers();
  return list.find(u => u.email === email && u.password === password) ?? null;
}

export async function registerUser({name, email, password, role = 'member', allUsers, onUsersUpdate }) {
  const data = await apiFetch('/users/register', {
    method: 'POST',
    body: JSON.stringify({ name,email, password, role }),
  });
  if (!data) {
  throw new Error("Registration failed. No response from backend.");
}

const newUser = {
  id: data.id || data.user_id || data.user?.id,
  email: data.email || email,
  name: data.name || email.split('@')[0],
  role: data.role || role,
  password
};

if (!newUser.id) {
  throw new Error("Registration failed. Backend did not return user id.");
}

  const current = allUsers?.length ? allUsers : getStoredUsers();
  const updated = current.find(u => u.email === email)
    ? current.map(u => u.email === email ? newUser : u)
    : [...current, newUser];
  saveUsers(updated);
  if (onUsersUpdate) onUsersUpdate(updated);
  return newUser;
}

// ── Projects ───────────────────────────────────────────────
export async function fetchProjects() {
  const data = await apiFetch('/projects');
  return toArray(data, 'projects') ?? [];
}

export async function createProject(name, description) {
  const data = await apiFetch('/projects', {
    method: 'POST',
    body: JSON.stringify({ name, description }),
  });
  return data ?? null; // null = failed, caller should handle
}

// ── Tasks ──────────────────────────────────────────────────
export async function fetchTasks() {
  const data = await apiFetch('/tasks');
  return toArray(data, 'tasks') ?? [];
}

export async function createTask(payload) {
  const data = await apiFetch('/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return data ?? null;
}

export async function updateTaskStatus(taskId, status) {
  const data = await apiFetch(`/tasks/${taskId}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
  return data ?? { id: taskId, status };
}

export async function deleteTask(taskId) {
  await apiFetch(`/tasks/${taskId}`, { method: 'DELETE' });
  return taskId;
}

// ── Dashboard ──────────────────────────────────────────────
export async function fetchDashboard(tasks) {
  const data = await apiFetch('/dashboard');
  if (data && typeof data.total === 'number') return data;
  const now = new Date();
  return {
    total:       tasks.length,
    todo:        tasks.filter(t => t.status === 'todo').length,
    in_progress: tasks.filter(t => t.status === 'in_progress').length,
    done:        tasks.filter(t => t.status === 'done').length,
    overdue:     tasks.filter(t => t.due_date && new Date(t.due_date) < now && t.status !== 'done').length,
  };
}


// ── Chat ───────────────────────────────────────────────────
export async function fetchProjectComments(projectId) {
  const data = await apiFetch(`/projects/${projectId}/comments`);
  return data || [];
}

export async function createProjectComment(projectId, userId, text) {
  return await apiFetch(`/projects/${projectId}/comments`, {
    method: 'POST',
    body: JSON.stringify({ text, user_id: userId }),
  });
}

export async function fetchTeamMessages() {
  const data = await apiFetch('/team/messages');
  return data || [];
}

export async function createTeamMessage(userId, text) {
  return await apiFetch('/team/messages', {
    method: 'POST',
    body: JSON.stringify({ text, user_id: userId }),
  });
}