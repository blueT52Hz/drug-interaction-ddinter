import { DatabaseSync } from 'node:sqlite';

interface DemoPairRow {
  reg1: string;
  name1: string;
  drug1: string;
  reg2: string;
  name2: string;
  drug2: string;
}

// Single-ingredient, fully mapped drugs, materialized once with an index
// (an inline CTE was re-evaluated for every join row and took minutes).
const CREATE_SINGLE_INGREDIENT_DRUGS_SQL = `
  DROP TABLE IF EXISTS temp.demo_single;
  CREATE TEMP TABLE demo_single AS
    SELECT d.registration_number AS reg, d.name AS name,
           MIN(i.ddinter_id) AS ddinter_id, MIN(i.ddinter_drug) AS ddinter_drug
    FROM drugs d JOIN drug_ingredients i ON i.registration_number = d.registration_number
    WHERE d.has_unmapped_ingredient = 0
    GROUP BY d.registration_number
    HAVING COUNT(*) = 1;
  CREATE INDEX temp.idx_demo_single ON demo_single(ddinter_id);`;

// One representative drug pair per distinct ingredient pair at the given level.
const DEMO_PAIR_SQL = `
  SELECT s1.reg AS reg1, s1.name AS name1, s1.ddinter_drug AS drug1,
         s2.reg AS reg2, s2.name AS name2, s2.ddinter_drug AS drug2
  FROM interactions x
  JOIN demo_single s1 ON s1.ddinter_id = x.ddinter_id_a
  JOIN demo_single s2 ON s2.ddinter_id = x.ddinter_id_b
  WHERE x.level = ?
  GROUP BY x.ddinter_id_a, x.ddinter_id_b
  ORDER BY s1.ddinter_drug, s2.ddinter_drug
  LIMIT 5`;

/** Print a few real drug pairs per level, used to write the demo script in README. */
export function printDemoDrugPairs(db: DatabaseSync): void {
  db.exec(CREATE_SINGLE_INGREDIENT_DRUGS_SQL);
  const statement = db.prepare(DEMO_PAIR_SQL);
  console.log('\nCặp thuốc gợi ý cho kịch bản demo:');
  for (const level of ['Major', 'Moderate', 'Unknown']) {
    const rows = statement.all(level) as unknown as DemoPairRow[];
    if (rows.length === 0) console.log(`[${level}] (không tìm thấy cặp phù hợp)`);
    for (const r of rows) {
      console.log(`[${level}] ${r.reg1} ${r.name1} (${r.drug1}) + ${r.reg2} ${r.name2} (${r.drug2})`);
    }
  }
}
