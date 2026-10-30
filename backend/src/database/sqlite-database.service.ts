import { Injectable, OnModuleDestroy } from '@nestjs/common';
import { existsSync } from 'node:fs';
import { DatabaseSync } from 'node:sqlite';
import { SQLITE_DB_PATH } from './sqlite-database-path';

/** Read-only handle to the demo SQLite database (built-in node:sqlite, no native module). */
@Injectable()
export class SqliteDatabaseService implements OnModuleDestroy {
  readonly db: DatabaseSync;

  constructor() {
    if (!existsSync(SQLITE_DB_PATH)) {
      throw new Error('Không tìm thấy data/pos-demo.sqlite. Hãy chạy: npm run import-data');
    }
    this.db = new DatabaseSync(SQLITE_DB_PATH, { readOnly: true });
  }

  onModuleDestroy(): void {
    try {
      this.db.close();
    } catch {
      // already closed - nothing to do
    }
  }
}
