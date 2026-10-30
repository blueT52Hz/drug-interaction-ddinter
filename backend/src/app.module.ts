import { Module } from '@nestjs/common';
import { DatabaseModule } from './database/database.module';
import { DrugWarningsModule } from './drug-warnings/drug-warnings.module';
import { DrugsModule } from './drugs/drugs.module';
import { InteractionsModule } from './interactions/interactions.module';

@Module({
  imports: [DatabaseModule, DrugsModule, InteractionsModule, DrugWarningsModule],
})
export class AppModule {}
