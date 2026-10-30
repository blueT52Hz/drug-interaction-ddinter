import { Injectable, InternalServerErrorException, Logger } from '@nestjs/common';
import { SqliteDatabaseService } from '../database/sqlite-database.service';
import { InteractionPair, SEVERITY_RANK, toInteractionLevel } from './interaction-pair.types';

interface CartIngredientRow {
  registration_number: string;
  name: string;
  ddinter_id: string;
  ddinter_drug: string;
}

interface InteractionRow {
  ddinter_id_a: string;
  ddinter_id_b: string;
  level: string;
  description: string | null;
  management: string | null;
}

interface CartIngredient {
  registrationNumber: string;
  drugName: string;
  ddinterDrug: string;
  order: number; // position of the drug in the request -> decides drug1/drug2
}

const placeholders = (n: number): string => Array.from({ length: n }, () => '?').join(',');

@Injectable()
export class InteractionsService {
  private readonly logger = new Logger(InteractionsService.name);

  constructor(private readonly database: SqliteDatabaseService) {}

  /** All interacting ingredient pairs between different drugs of the cart, most severe first. */
  check(registrationNumbers: string[]): InteractionPair[] {
    const regs = [...new Set(registrationNumbers)];
    try {
      const byDdinterId = this.loadCartIngredients(regs);
      if (byDdinterId.size === 0) return [];
      const ids = [...byDdinterId.keys()];
      // same id set on both sides -> covers pairs stored in either direction
      const interactions = this.database.db
        .prepare(
          `SELECT ddinter_id_a, ddinter_id_b, level, description, management FROM interactions
           WHERE ddinter_id_a IN (${placeholders(ids.length)}) AND ddinter_id_b IN (${placeholders(ids.length)})`,
        )
        .all(...ids, ...ids) as unknown as InteractionRow[];
      return this.buildPairs(interactions, byDdinterId);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      this.logger.error(`check(${regs.join(',')}) failed: ${message}`);
      if (message.includes('no such column') || message.includes('no such table')) {
        // DB was built before the interaction detail columns existed
        throw new InternalServerErrorException('CSDL cũ, thiếu dữ liệu chi tiết tương tác. Hãy dừng backend rồi chạy: npm run import-data');
      }
      throw new InternalServerErrorException('Lỗi truy vấn cơ sở dữ liệu');
    }
  }

  /** DDInter id -> ingredients of cart drugs carrying that id (unknown registration numbers are ignored). */
  private loadCartIngredients(regs: string[]): Map<string, CartIngredient[]> {
    const byDdinterId = new Map<string, CartIngredient[]>();
    if (regs.length === 0) return byDdinterId;
    const order = new Map(regs.map((reg, index) => [reg, index]));
    const rows = this.database.db
      .prepare(
        `SELECT i.registration_number, d.name, i.ddinter_id, i.ddinter_drug
         FROM drug_ingredients i JOIN drugs d ON d.registration_number = i.registration_number
         WHERE i.ddinter_id IS NOT NULL AND i.registration_number IN (${placeholders(regs.length)})`,
      )
      .all(...regs) as unknown as CartIngredientRow[];
    for (const row of rows) {
      const list = byDdinterId.get(row.ddinter_id) ?? [];
      list.push({
        registrationNumber: row.registration_number,
        drugName: row.name,
        ddinterDrug: row.ddinter_drug,
        order: order.get(row.registration_number) ?? 0,
      });
      byDdinterId.set(row.ddinter_id, list);
    }
    return byDdinterId;
  }

  private buildPairs(interactions: InteractionRow[], byDdinterId: Map<string, CartIngredient[]>): InteractionPair[] {
    const pairs = new Map<string, InteractionPair>();
    for (const x of interactions) {
      for (const a of byDdinterId.get(x.ddinter_id_a) ?? []) {
        for (const b of byDdinterId.get(x.ddinter_id_b) ?? []) {
          if (a.registrationNumber === b.registrationNumber) continue; // same drug: out of scope
          const [first, second] = a.order <= b.order ? [a, b] : [b, a];
          const key = `${first.registrationNumber}|${second.registrationNumber}|${first.ddinterDrug}|${second.ddinterDrug}`;
          if (pairs.has(key)) continue;
          pairs.set(key, {
            drug1: { registrationNumber: first.registrationNumber, name: first.drugName },
            drug2: { registrationNumber: second.registrationNumber, name: second.drugName },
            ingredient1: first.ddinterDrug,
            ingredient2: second.ddinterDrug,
            level: toInteractionLevel(x.level),
            description: x.description ?? '',
            management: x.management ?? '',
          });
        }
      }
    }
    return [...pairs.values()].sort((p, q) => SEVERITY_RANK[q.level] - SEVERITY_RANK[p.level]);
  }
}
