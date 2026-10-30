import { Injectable, InternalServerErrorException, Logger } from '@nestjs/common';
import { SqliteDatabaseService } from '../database/sqlite-database.service';
import { SEVERITY_RANK, toInteractionLevel } from '../interactions/interaction-pair.types';
import { DiseaseWarning, DrugWarnings, FoodWarning } from './drug-warning.types';

interface DiseaseRow {
  ingredient: string;
  disease_name: string;
  severity: string;
  description: string | null;
}

interface FoodRow {
  ingredient: string;
  food_name: string;
  severity: string;
  description: string | null;
  management: string | null;
}

const bySeverityDesc = <T extends { level: keyof typeof SEVERITY_RANK }>(a: T, b: T): number =>
  SEVERITY_RANK[b.level] - SEVERITY_RANK[a.level];

@Injectable()
export class DrugWarningsService {
  private readonly logger = new Logger(DrugWarningsService.name);

  constructor(private readonly database: SqliteDatabaseService) {}

  /** Drug-disease and drug-food warnings of every mapped ingredient of the drug, most severe first. */
  getWarnings(registrationNumber: string): DrugWarnings {
    try {
      return {
        registrationNumber,
        diseases: this.loadDiseaseWarnings(registrationNumber),
        foods: this.loadFoodWarnings(registrationNumber),
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      this.logger.error(`getWarnings(${registrationNumber}) failed: ${message}`);
      if (message.includes('no such table')) {
        // DB was built before drug-disease / drug-food data existed
        throw new InternalServerErrorException(
          'CSDL chưa có dữ liệu lưu ý bệnh lý/thức ăn. Hãy dừng backend rồi chạy: npm run import-data',
        );
      }
      throw new InternalServerErrorException('Lỗi truy vấn cơ sở dữ liệu');
    }
  }

  private loadDiseaseWarnings(registrationNumber: string): DiseaseWarning[] {
    const rows = this.database.db
      .prepare(
        `SELECT DISTINCT i.ddinter_drug AS ingredient, d.disease_name, d.severity, d.description
         FROM drug_ingredients i JOIN drug_disease_interactions d ON d.ddinter_id = i.ddinter_id
         WHERE i.registration_number = ? AND i.ddinter_id IS NOT NULL`,
      )
      .all(registrationNumber) as unknown as DiseaseRow[];
    return rows
      .map((r) => ({
        ingredient: r.ingredient,
        diseaseName: r.disease_name,
        level: toInteractionLevel(r.severity),
        description: r.description ?? '',
      }))
      .sort(bySeverityDesc);
  }

  private loadFoodWarnings(registrationNumber: string): FoodWarning[] {
    const rows = this.database.db
      .prepare(
        `SELECT DISTINCT i.ddinter_drug AS ingredient, f.food_name, f.severity, f.description, f.management
         FROM drug_ingredients i JOIN drug_food_interactions f ON f.ddinter_id = i.ddinter_id
         WHERE i.registration_number = ? AND i.ddinter_id IS NOT NULL`,
      )
      .all(registrationNumber) as unknown as FoodRow[];
    // group foods that share the same ingredient + severity + text
    const grouped = new Map<string, FoodWarning>();
    for (const r of rows) {
      const key = `${r.ingredient}|${r.severity}|${r.description}|${r.management}`;
      const existing = grouped.get(key);
      if (existing) {
        if (!existing.foods.includes(r.food_name)) existing.foods.push(r.food_name);
        continue;
      }
      grouped.set(key, {
        ingredient: r.ingredient,
        foods: [r.food_name],
        level: toInteractionLevel(r.severity),
        description: r.description ?? '',
        management: r.management ?? '',
      });
    }
    return [...grouped.values()].sort(bySeverityDesc);
  }
}
