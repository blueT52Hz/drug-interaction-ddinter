import { Global, Module } from '@nestjs/common';
import { SqliteDatabaseService } from './sqlite-database.service';

/** Global module so feature modules can inject SqliteDatabaseService without importing it. */
@Global()
@Module({
  providers: [SqliteDatabaseService],
  exports: [SqliteDatabaseService],
})
export class DatabaseModule {}
