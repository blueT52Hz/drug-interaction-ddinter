import { Module } from '@nestjs/common';
import { DrugWarningsController } from './drug-warnings.controller';
import { DrugWarningsService } from './drug-warnings.service';

@Module({
  controllers: [DrugWarningsController],
  providers: [DrugWarningsService],
})
export class DrugWarningsModule {}
