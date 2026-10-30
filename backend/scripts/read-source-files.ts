/**
 * Readers for the source data files under <repo>/data used by the import script.
 * Every value is read as a string so registration numbers keep their leading zeros.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { parse } from 'csv-parse/sync';
import * as XLSX from 'xlsx';

const DATA_DIR = resolve(__dirname, '../../data');
export const NATIONAL_DRUG_XLSX = resolve(DATA_DIR, 'national_drug.xlsx');
export const INGREDIENT_MAPPING_CSV = resolve(DATA_DIR, 'mapping/national-drug-ddinter-mapping.csv');
// "final" = merged pairs + DDInter detail text (Interaction, Management)
export const INTERACTIONS_CSV = resolve(DATA_DIR, 'ddinter/ddinter_interactions_final.csv');
export const DRUG_DISEASE_CSV = resolve(DATA_DIR, 'ddinter/drug_disease_interactions.csv');
export const DRUG_FOOD_CSV = resolve(DATA_DIR, 'ddinter/drug_food_interactions.csv');

export interface DrugDiseaseRow {
  ddinterId: string;
  drugName: string;
  severity: string;
  diseaseName: string;
  description: string;
}

export interface DrugFoodRow {
  ddinterId: string;
  drugName: string;
  severity: string;
  foodName: string;
  description: string;
  management: string;
  mechanism: string;
}

export interface NationalDrugRow {
  registrationNumber: string;
  name: string;
  manufacturer: string;
  packaging: string;
  ingredientText: string;
}

export interface MappingRow {
  registrationNumber: string;
  ingredientOrder: number;
  ingredientName: string;
  ddinterId: string; // '' when the ingredient is not mapped
  ddinterDrug: string;
}

export interface InteractionRow {
  ddinterIdA: string;
  drugA: string;
  ddinterIdB: string;
  drugB: string;
  level: string;
  description: string; // '' when DDInter has no text
  management: string;
}

/** DDInter writes "None" / "-" when a pair has no description or management text. */
const detailText = (value: string | undefined): string => {
  const text = (value ?? '').trim();
  return text === 'None' || text === '-' ? '' : text;
};

/** Collapse whitespace/newlines in xlsx headers ("Tên thuốc (*) " -> "Tên thuốc (*)"). */
const collapse = (s: string): string => s.replace(/\s+/g, ' ').trim();

function readCsv(path: string): Record<string, string>[] {
  return parse(readFileSync(path, 'utf8'), { bom: true, columns: true, skip_empty_lines: true });
}

export function readNationalDrugs(): NationalDrugRow[] {
  const workbook = XLSX.readFile(NATIONAL_DRUG_XLSX);
  const sheet = workbook.Sheets['DanhSach'];
  if (!sheet) throw new Error('Không tìm thấy sheet DanhSach trong national_drug.xlsx');
  const rows = XLSX.utils.sheet_to_json<Record<string, unknown>>(sheet, { raw: false, defval: '' });
  return rows
    .map((raw) => {
      const row: Record<string, string> = {};
      for (const [key, value] of Object.entries(raw)) row[collapse(key)] = String(value ?? '').trim();
      return {
        registrationNumber: row['Số đăng ký lưu hành (*)'] ?? '',
        name: row['Tên thuốc (*)'] ?? '',
        manufacturer: row['Nhà sản xuất'] ?? '',
        packaging: row['Quy cách đóng gói'] ?? '',
        ingredientText: row['Thành phần'] ?? '',
      };
    })
    .filter((d) => d.registrationNumber !== '');
}

export function readIngredientMappingRows(): MappingRow[] {
  return readCsv(INGREDIENT_MAPPING_CSV).map((r) => ({
    registrationNumber: (r.registration_number ?? '').trim(),
    ingredientOrder: Number(r.ingredient_order) || 0,
    ingredientName: r.ingredient_name ?? '',
    ddinterId: (r.ddinter_id ?? '').trim(),
    ddinterDrug: r.ddinter_drug ?? '',
  }));
}

/** Drug-disease warnings (the long `references` column is not needed by the UI and is dropped). */
export function readDrugDiseaseRows(): DrugDiseaseRow[] {
  return readCsv(DRUG_DISEASE_CSV).map((r) => ({
    ddinterId: (r.drug_id ?? '').trim(),
    drugName: r.drug_name ?? '',
    severity: (r.severity ?? '').trim(),
    diseaseName: r.disease_name ?? '',
    description: r.description ?? '',
  }));
}

/** Drug-food warnings (references dropped). */
export function readDrugFoodRows(): DrugFoodRow[] {
  return readCsv(DRUG_FOOD_CSV).map((r) => ({
    ddinterId: (r.drug_id ?? '').trim(),
    drugName: r.drug_name ?? '',
    severity: (r.severity ?? '').trim(),
    foodName: r.food_name ?? '',
    description: r.description ?? '',
    management: r.management ?? '',
    mechanism: r.mechanism ?? '',
  }));
}

export function readInteractionRows(): InteractionRow[] {
  return readCsv(INTERACTIONS_CSV).map((r) => ({
    ddinterIdA: r.DDInterID_A,
    drugA: r.Drug_A,
    ddinterIdB: r.DDInterID_B,
    drugB: r.Drug_B,
    level: r.Level,
    description: detailText(r.Interaction),
    management: detailText(r.Management),
  }));
}
