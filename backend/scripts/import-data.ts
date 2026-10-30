/**
 * Build backend/data/pos-demo.sqlite from:
 *   data/national_drug.xlsx, data/mapping/national-drug-ddinter-mapping.csv,
 *   data/ddinter/ddinter_interactions_final.csv, data/ddinter/drug_disease_interactions.csv,
 *   data/ddinter/drug_food_interactions.csv
 * Usage: npm run import-data
 */
import { existsSync, mkdirSync, rmSync } from 'node:fs';
import { dirname } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { normalizeForSearch } from '../src/common/vietnamese-text-normalizer';
import { SQLITE_DB_PATH } from '../src/database/sqlite-database-path';
import { createSqliteSchema } from './create-sqlite-schema';
import { printDemoDrugPairs } from './print-demo-drug-pairs';
import {
  MappingRow,
  readDrugDiseaseRows,
  readDrugFoodRows,
  readIngredientMappingRows,
  readInteractionRows,
  readNationalDrugs,
} from './read-source-files';

/** Registration numbers that have at least one ingredient without a DDInter id. */
function findDrugsWithUnmappedIngredient(mappingRows: MappingRow[]): {
  unmapped: Set<string>;
  withMapping: Set<string>;
} {
  const unmapped = new Set<string>();
  const withMapping = new Set<string>();
  for (const row of mappingRows) {
    withMapping.add(row.registrationNumber);
    if (!row.ddinterId) unmapped.add(row.registrationNumber); // includes no_ingredient rows
  }
  return { unmapped, withMapping };
}

function importAll(db: DatabaseSync): void {
  console.log('Đang đọc file nguồn...');
  const drugs = readNationalDrugs();
  const mappingRows = readIngredientMappingRows();
  const interactionRows = readInteractionRows();
  const diseaseRows = readDrugDiseaseRows();
  const foodRows = readDrugFoodRows();
  const { unmapped, withMapping } = findDrugsWithUnmappedIngredient(mappingRows);

  createSqliteSchema(db);
  const insertDrug = db.prepare(
    `INSERT OR IGNORE INTO drugs (registration_number, name, manufacturer, packaging, ingredient_text,
       has_unmapped_ingredient, search_text) VALUES (?, ?, ?, ?, ?, ?, ?)`,
  );
  const insertIngredient = db.prepare(
    `INSERT INTO drug_ingredients (registration_number, ingredient_order, ingredient_name, ddinter_id, ddinter_drug)
     VALUES (?, ?, ?, ?, ?)`,
  );
  const insertInteraction = db.prepare(
    `INSERT INTO interactions (ddinter_id_a, ddinter_id_b, drug_a, drug_b, level, description, management)
     VALUES (?, ?, ?, ?, ?, ?, ?)`,
  );
  const insertDisease = db.prepare(
    `INSERT INTO drug_disease_interactions (ddinter_id, drug_name, severity, disease_name, description)
     VALUES (?, ?, ?, ?, ?)`,
  );
  const insertFood = db.prepare(
    `INSERT INTO drug_food_interactions (ddinter_id, drug_name, severity, food_name, description, management, mechanism)
     VALUES (?, ?, ?, ?, ?, ?, ?)`,
  );

  db.exec('BEGIN');
  try {
    for (const d of drugs) {
      const hasUnmapped = unmapped.has(d.registrationNumber) || !withMapping.has(d.registrationNumber);
      insertDrug.run(d.registrationNumber, d.name, d.manufacturer, d.packaging, d.ingredientText,
        hasUnmapped ? 1 : 0, normalizeForSearch(`${d.name} ${d.registrationNumber}`));
    }
    for (const m of mappingRows) {
      if (m.ingredientOrder === 0) continue; // no_ingredient placeholder row, no actual ingredient
      insertIngredient.run(m.registrationNumber, m.ingredientOrder, m.ingredientName,
        m.ddinterId || null, m.ddinterDrug || null);
    }
    for (const i of interactionRows) {
      insertInteraction.run(i.ddinterIdA, i.ddinterIdB, i.drugA, i.drugB, i.level,
        i.description || null, i.management || null);
    }
    for (const d of diseaseRows) {
      if (d.ddinterId) insertDisease.run(d.ddinterId, d.drugName, d.severity, d.diseaseName, d.description);
    }
    for (const f of foodRows) {
      if (f.ddinterId) insertFood.run(f.ddinterId, f.drugName, f.severity, f.foodName, f.description, f.management, f.mechanism);
    }
    db.exec('COMMIT');
  } catch (error) {
    db.exec('ROLLBACK');
    throw error;
  }

  for (const table of ['drugs', 'drug_ingredients', 'interactions', 'drug_disease_interactions', 'drug_food_interactions']) {
    const { n } = db.prepare(`SELECT COUNT(*) AS n FROM ${table}`).get() as { n: number };
    console.log(`${table}: ${n}`);
  }
}

function main(): void {
  mkdirSync(dirname(SQLITE_DB_PATH), { recursive: true });
  if (existsSync(SQLITE_DB_PATH)) rmSync(SQLITE_DB_PATH);
  const db = new DatabaseSync(SQLITE_DB_PATH);
  try {
    importAll(db);
    printDemoDrugPairs(db);
    console.log(`Đã tạo ${SQLITE_DB_PATH}`);
  } finally {
    db.close();
  }
}

try {
  main();
} catch (error) {
  console.error('Import thất bại:', error instanceof Error ? error.message : error);
  process.exitCode = 1;
}
