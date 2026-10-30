import { DatabaseSync } from 'node:sqlite';

/** Drop and recreate the demo tables (drugs, ingredients, drug-drug / drug-disease / drug-food interactions). */
export function createSqliteSchema(db: DatabaseSync): void {
  db.exec(`
    DROP TABLE IF EXISTS drug_food_interactions;
    DROP TABLE IF EXISTS drug_disease_interactions;
    DROP TABLE IF EXISTS interactions;
    DROP TABLE IF EXISTS drug_ingredients;
    DROP TABLE IF EXISTS drugs;

    CREATE TABLE drugs (
      registration_number TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      manufacturer TEXT,
      packaging TEXT,
      ingredient_text TEXT,
      has_unmapped_ingredient INTEGER NOT NULL,
      search_text TEXT NOT NULL
    );

    CREATE TABLE drug_ingredients (
      registration_number TEXT NOT NULL,
      ingredient_order INTEGER NOT NULL,
      ingredient_name TEXT,
      ddinter_id TEXT,      -- NULL when the ingredient could not be mapped to DDInter
      ddinter_drug TEXT
    );
    CREATE INDEX idx_drug_ingredients_reg ON drug_ingredients(registration_number);

    CREATE TABLE interactions (
      ddinter_id_a TEXT NOT NULL,
      ddinter_id_b TEXT NOT NULL,
      drug_a TEXT,
      drug_b TEXT,
      level TEXT NOT NULL,
      description TEXT,     -- DDInter "Interaction" text, NULL when missing
      management TEXT
    );
    CREATE INDEX idx_interactions_pair ON interactions(ddinter_id_a, ddinter_id_b);

    CREATE TABLE drug_disease_interactions (
      ddinter_id TEXT NOT NULL,
      drug_name TEXT,
      severity TEXT NOT NULL,
      disease_name TEXT NOT NULL,
      description TEXT
    );
    CREATE INDEX idx_drug_disease_id ON drug_disease_interactions(ddinter_id);

    CREATE TABLE drug_food_interactions (
      ddinter_id TEXT NOT NULL,
      drug_name TEXT,
      severity TEXT NOT NULL,
      food_name TEXT NOT NULL,
      description TEXT,
      management TEXT,
      mechanism TEXT
    );
    CREATE INDEX idx_drug_food_id ON drug_food_interactions(ddinter_id);
  `);
}
