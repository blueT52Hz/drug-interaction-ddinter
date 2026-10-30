import { Injectable, InternalServerErrorException } from '@nestjs/common';
import { normalizeForSearch } from '../common/vietnamese-text-normalizer';
import { SqliteDatabaseService } from '../database/sqlite-database.service';
import { DrugIngredient, DrugPage, DrugSearchResult } from './drug-search-result.types';
import { FEATURED_DEMO_REGISTRATION_NUMBERS } from './featured-demo-drugs';

const MAX_QUERY_LENGTH = 100;
const MIN_QUERY_LENGTH = 2;
const RESULT_LIMIT = 20;
const DRUG_COLUMNS = 'registration_number, name, manufacturer, packaging, has_unmapped_ingredient';

interface DrugRow {
  registration_number: string;
  name: string;
  manufacturer: string | null;
  packaging: string | null;
  has_unmapped_ingredient: number;
}

interface IngredientRow {
  registration_number: string;
  ingredient_name: string | null;
  ddinter_drug: string | null;
}

/** Escape LIKE wildcards so "%" or "_" typed by the user are matched literally. */
const escapeLike = (s: string): string => s.replace(/[\\%_]/g, (c) => `\\${c}`);

@Injectable()
export class DrugsService {
  constructor(private readonly database: SqliteDatabaseService) {}

  /** Accent-insensitive search by drug name or registration number; max 20 results. */
  search(query: string): DrugSearchResult[] {
    const normalized = normalizeForSearch(query.slice(0, MAX_QUERY_LENGTH));
    if (normalized.length < MIN_QUERY_LENGTH) return [];
    const escaped = escapeLike(normalized);
    try {
      const drugs = this.database.db
        .prepare(
          `SELECT ${DRUG_COLUMNS} FROM drugs
           WHERE search_text LIKE ? ESCAPE '\\'
           ORDER BY CASE WHEN search_text LIKE ? ESCAPE '\\' THEN 0 ELSE 1 END, name
           LIMIT ${RESULT_LIMIT}`,
        )
        .all(`%${escaped}%`, `${escaped}%`) as unknown as DrugRow[];
      return this.toResults(drugs);
    } catch (error) {
      throw new InternalServerErrorException('Lỗi truy vấn cơ sở dữ liệu');
    }
  }

  /**
   * Default product list shown before typing (like KiotViet's product grid):
   * only drugs with full DDInter data, featured demo drugs first, then by name.
   */
  list(page: number, pageSize: number): DrugPage {
    const featured = FEATURED_DEMO_REGISTRATION_NUMBERS;
    const featuredOrder = featured.length
      ? `CASE registration_number ${featured.map((_, i) => `WHEN ? THEN ${i}`).join(' ')} ELSE ${featured.length} END`
      : '0';
    try {
      const { total } = this.database.db
        .prepare('SELECT COUNT(*) AS total FROM drugs WHERE has_unmapped_ingredient = 0')
        .get() as { total: number };
      const drugs = this.database.db
        .prepare(
          `SELECT ${DRUG_COLUMNS} FROM drugs WHERE has_unmapped_ingredient = 0
           ORDER BY ${featuredOrder}, name LIMIT ? OFFSET ?`,
        )
        .all(...featured, pageSize, (page - 1) * pageSize) as unknown as DrugRow[];
      return { items: this.toResults(drugs), total, page, pageSize };
    } catch (error) {
      throw new InternalServerErrorException('Lỗi truy vấn cơ sở dữ liệu');
    }
  }

  private toResults(drugs: DrugRow[]): DrugSearchResult[] {
    const ingredientsByDrug = this.loadIngredients(drugs.map((d) => d.registration_number));
    return drugs.map((d) => ({
      registrationNumber: d.registration_number,
      name: d.name,
      manufacturer: d.manufacturer ?? '',
      packaging: d.packaging ?? '',
      ingredients: ingredientsByDrug.get(d.registration_number) ?? [],
      hasUnmappedIngredient: d.has_unmapped_ingredient === 1,
    }));
  }

  private loadIngredients(registrationNumbers: string[]): Map<string, DrugIngredient[]> {
    const byDrug = new Map<string, DrugIngredient[]>();
    if (registrationNumbers.length === 0) return byDrug;
    const placeholders = registrationNumbers.map(() => '?').join(',');
    const rows = this.database.db
      .prepare(
        `SELECT registration_number, ingredient_name, ddinter_drug FROM drug_ingredients
         WHERE registration_number IN (${placeholders}) ORDER BY registration_number, ingredient_order`,
      )
      .all(...registrationNumbers) as unknown as IngredientRow[];
    for (const row of rows) {
      const list = byDrug.get(row.registration_number) ?? [];
      list.push({ name: row.ingredient_name ?? '', ddinterDrug: row.ddinter_drug });
      byDrug.set(row.registration_number, list);
    }
    return byDrug;
  }
}
