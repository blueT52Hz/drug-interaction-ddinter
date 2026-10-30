import { resolve } from 'node:path';

/**
 * Path of the SQLite file produced by `npm run import-data` (backend/data/pos-demo.sqlite).
 * Kept free of Nest imports so the import script can use it without reflect-metadata.
 */
export const SQLITE_DB_PATH = resolve(__dirname, '../../data/pos-demo.sqlite');
