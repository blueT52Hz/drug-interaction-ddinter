// Copied verbatim from the backend contracts:
// backend/src/drugs/drug-search-result.types.ts and backend/src/interactions/interaction-pair.types.ts

export interface DrugIngredient {
  name: string;
  /** DDInter drug name, null when the ingredient is not mapped to DDInter */
  ddinterDrug: string | null;
}

export interface DrugSearchResult {
  registrationNumber: string;
  name: string;
  manufacturer: string;
  packaging: string;
  ingredients: DrugIngredient[];
  hasUnmappedIngredient: boolean;
}

export interface DrugPage {
  items: DrugSearchResult[];
  total: number;
  page: number;
  pageSize: number;
}

export type InteractionLevel = 'Major' | 'Moderate' | 'Minor' | 'Unknown';

export interface DrugRef {
  registrationNumber: string;
  name: string;
}

export interface InteractionPair {
  drug1: DrugRef;
  drug2: DrugRef;
  ingredient1: string;
  ingredient2: string;
  level: InteractionLevel;
  /** DDInter mechanism/effect text (English), '' when DDInter has none */
  description: string;
  /** DDInter management advice (English), '' when DDInter has none */
  management: string;
}

// Copied from backend/src/drug-warnings/drug-warning.types.ts
export interface DiseaseWarning {
  ingredient: string;
  diseaseName: string;
  level: InteractionLevel;
  description: string;
}

export interface FoodWarning {
  ingredient: string;
  foods: string[];
  level: InteractionLevel;
  description: string;
  management: string;
}

export interface DrugWarnings {
  registrationNumber: string;
  diseases: DiseaseWarning[];
  foods: FoodWarning[];
}
