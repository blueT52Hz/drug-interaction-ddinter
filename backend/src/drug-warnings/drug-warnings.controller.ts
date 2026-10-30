import { BadRequestException, Controller, Get, Query } from '@nestjs/common';
import { DrugWarnings } from './drug-warning.types';
import { DrugWarningsService } from './drug-warnings.service';

@Controller('drug-warnings')
export class DrugWarningsController {
  constructor(private readonly drugWarningsService: DrugWarningsService) {}

  /** GET /api/drug-warnings?registrationNumber=... (unknown numbers return empty lists) */
  @Get()
  get(@Query('registrationNumber') registrationNumber: unknown): DrugWarnings {
    if (typeof registrationNumber !== 'string' || registrationNumber.trim() === '') {
      throw new BadRequestException('Thiếu registrationNumber');
    }
    return this.drugWarningsService.getWarnings(registrationNumber.trim());
  }
}
