import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import { Low } from 'lowdb';
import { JSONFile } from 'lowdb/node';
import fs from 'fs';
import path from 'path';

const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;
const API_KEY = process.env.API_KEY || 'dev_local';
const DB_PATH = process.env.DB_PATH || './data/db.json';

fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });

const adapter = new JSONFile(DB_PATH);
const db = new Low(adapter, { reports: [] });
await db.read();
db.data ||= { reports: [] };

const app = express();
app.use(cors());
app.use(express.json({ limit: '256kb' }));

// Static Admin Dashboard
const publicDir = path.join(process.cwd(), 'public');
app.use('/admin', express.static(path.join(publicDir, 'admin')));

// Simple API key middleware
app.use('/api', (req, res, next) => {
  const key = req.header('X-API-Key');
  if (!key || key !== API_KEY) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
});

app.post('/api/v1/report', async (req, res) => {
  const { machine_id, hostname, os, timestamp, checks } = req.body || {};
  if (!machine_id || !timestamp || !checks) {
    return res.status(400).json({ error: 'Missing fields' });
  }
  db.data.reports.push({
    machine_id,
    hostname: hostname || null,
    os: os || null,
    ts: Number(timestamp),
    checks
  });
  await db.write();
  return res.json({ ok: true });
});

function getLatestPerMachine(filters = {}) {
  const { os, hasIssues, q } = filters;
  const reports = db.data.reports;
  // Map of latest by machine_id
  const latest = new Map();
  for (const r of reports) {
    const prev = latest.get(r.machine_id);
    if (!prev || r.ts > prev.ts) latest.set(r.machine_id, r);
  }
  let result = Array.from(latest.values()).map((r) => ({
    machine_id: r.machine_id,
    hostname: r.hostname,
    os: r.os,
    timestamp: r.ts,
    checks: r.checks
  }));

  if (os) result = result.filter((x) => (x.os || '').toLowerCase() === String(os).toLowerCase());
  if (typeof hasIssues !== 'undefined') {
    const target = String(hasIssues).toLowerCase() === 'true';
    result = result.filter((x) => {
      const issues = Object.values(x.checks).some((c) => (c?.status || 'unknown') === 'issue');
      return target ? issues : !issues;
    });
  }
  if (q) {
    const s = String(q).toLowerCase();
    result = result.filter((x) =>
      (x.machine_id || '').toLowerCase().includes(s) ||
      (x.hostname || '').toLowerCase().includes(s)
    );
  }
  return result;
}

app.get('/api/v1/machines', (req, res) => {
  const { os, hasIssues, q } = req.query;
  const data = getLatestPerMachine({ os, hasIssues, q });
  res.json({ count: data.length, items: data });
});

app.get('/api/v1/export.csv', (req, res) => {
  const { os, hasIssues, q } = req.query;
  const data = getLatestPerMachine({ os, hasIssues, q });
  const headers = [
    'machine_id', 'hostname', 'os', 'timestamp',
    'disk_encryption.status', 'os_updates.status', 'antivirus.status', 'sleep_policy.status'
  ];
  const rows = [headers.join(',')];
  for (const item of data) {
    const c = item.checks || {};
    const line = [
      item.machine_id,
      item.hostname || '',
      item.os || '',
      String(item.timestamp),
      c?.disk_encryption?.status || 'unknown',
      c?.os_updates?.status || 'unknown',
      c?.antivirus?.status || 'unknown',
      c?.sleep_policy?.status || 'unknown',
    ].map((v) => String(v).replaceAll('"', '""'))
     .map((v) => /[,\n]/.test(v) ? `"${v}"` : v)
     .join(',');
    rows.push(line);
  }
  res.setHeader('Content-Type', 'text/csv');
  res.send(rows.join('\n'));
});

app.get('/api/v1/machines/:id', (req, res) => {
  const id = req.params.id;
  const rows = db.data.reports
    .filter((r) => r.machine_id === id)
    .sort((a, b) => b.ts - a.ts)
    .slice(0, 500)
    .map((r) => ({ timestamp: r.ts, hostname: r.hostname, os: r.os, checks: r.checks }));
  res.json({ machine_id: id, count: rows.length, items: rows });
});

app.get('/health', (_req, res) => res.json({ ok: true }));

// Admin API (read-only) that does not require client API key
app.get('/admin/api/machines', (req, res) => {
  const { os, hasIssues, q } = req.query;
  const data = getLatestPerMachine({ os, hasIssues, q });
  res.json({ count: data.length, items: data });
});

app.get('/admin/api/machines/:id', (req, res) => {
  const id = req.params.id;
  const rows = db.data.reports
    .filter((r) => r.machine_id === id)
    .sort((a, b) => b.ts - a.ts)
    .slice(0, 200)
    .map((r) => ({ timestamp: r.ts, hostname: r.hostname, os: r.os, checks: r.checks }));
  res.json({ machine_id: id, count: rows.length, items: rows });
});

app.listen(PORT, () => {
  console.log(`Compliance Monitor server listening on http://localhost:${PORT}`);
});
