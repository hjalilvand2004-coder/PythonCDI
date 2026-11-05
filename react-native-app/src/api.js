const SERVER = 'http://188.212.96.235:8085';

export async function login(uid, password) {
  const form = new URLSearchParams();
  form.append('uid', uid);
  form.append('password', password);
  try {
    const r = await fetch(`${SERVER}/login`, {
      method: 'POST',
      body: form,
      redirect: 'manual',
      credentials: 'include',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    if (r.status === 0 || r.type === 'opaqueredirect' || r.status === 302) {
      return { success: true };
    }
    return { success: false, error: 'نام کاربری یا رمز نادرست' };
  } catch (e) {
    return { success: false, error: e.message };
  }
}

export async function getPool() {
  try {
    const r = await fetch(`${SERVER}/api/pool`, { credentials: 'include' });
    if (!r.ok) return [];
    const data = await r.json();
    return data.cases || [];
  } catch {
    return [];
  }
}

export async function claimCase(hid) {
  try {
    const form = new URLSearchParams();
    const r = await fetch(`${SERVER}/assistant/claim/${hid}`, {
      method: 'POST', body: form, credentials: 'include',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return r.ok || r.status === 302 || r.type === 'opaqueredirect';
  } catch {
    return false;
  }
}

export async function getCaseDetail(hid) {
  try {
    const r = await fetch(`${SERVER}/api/assessment/${hid}`, { credentials: 'include' });
    if (!r.ok) return null;
    const data = await r.json();
    return data.assessments?.[hid] || null;
  } catch {
    return null;
  }
}

export async function submitSatisfaction(hid, scores, comment) {
  try {
    const form = new URLSearchParams();
    Object.entries(scores).forEach(([k, v]) => form.append(`score_${k}`, v));
    form.append('comment', comment);
    const r = await fetch(`${SERVER}/m/satisfaction/${hid}`, {
      method: 'POST', body: form, credentials: 'include',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return r.ok;
  } catch {
    return false;
  }
}

export function openQuestionnaire(hid, role) {
  const url = hid
    ? `${SERVER}/questionnaire/${hid}?role=${role}`
    : `${SERVER}/questionnaire?action=register`;
  // In React Native, we use Linking
  const { Linking } = require('react-native');
  Linking.openURL(url);
}

export function getServerUrl() { return SERVER; }
