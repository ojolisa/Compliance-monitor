#!/usr/bin/env node
// Optional helper to initialize the database schema (already created by index.js).
import 'dotenv/config';
import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';

const DB_PATH = process.env.DB_PATH || './data/compliance.db';
fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });
const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');
db.exec(`
CREATE TABLE IF NOT EXISTS reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  machine_id TEXT NOT NULL,
  hostname TEXT,
  os TEXT,
  ts INTEGER NOT NULL,
  checks_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reports_machine_ts ON reports(machine_id, ts DESC);
`);
console.log('Database initialized at', DB_PATH);
