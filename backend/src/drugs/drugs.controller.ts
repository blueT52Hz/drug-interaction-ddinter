import { Controller, Get, Query } from '@nestjs/common';
import { DrugPage, DrugSearchResult } from './drug-search-result.types';
import { DrugsService } from './drugs.service';

const DEFAULT_PAGE_SIZE = 18; // 3 columns x 6 rows, like the KiotViet product grid
const MAX_PAGE_SIZE = 60;

/** Parse a positive integer query param, falling back to `fallback` and clamping to `max`. */
function toPositiveInt(value: unknown, fallback: number, max = Number.MAX_SAFE_INTEGER): number {
  const n = typeof value === 'string' ? Number.parseInt(value, 10) : NaN;
  return Number.isFinite(n) && n >= 1 ? Math.min(n, max) : fallback;
}

@Controller('drugs')
export class DrugsController {
  constructor(private readonly drugsService: DrugsService) {}

  /** GET /api/drugs?page=1&pageSize=18 - default product list before the user types */
  @Get()
  list(@Query('page') page: unknown, @Query('pageSize') pageSize: unknown): DrugPage {
    return this.drugsService.list(toPositiveInt(page, 1), toPositiveInt(pageSize, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE));
  }

  /** GET /api/drugs/search?q=... */
  @Get('search')
  search(@Query('q') q: unknown): DrugSearchResult[] {
    return this.drugsService.search(typeof q === 'string' ? q : '');
  }
}
