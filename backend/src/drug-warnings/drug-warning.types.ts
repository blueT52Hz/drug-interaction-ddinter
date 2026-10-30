import { InteractionLevel } from '../interactions/interaction-pair.types';

/** DDInter drug-disease warning for one ingredient of the drug. */
export interface DiseaseWarning {
  /** DDInter drug name of the ingredient */
  ingredient: string;
  diseaseName: string;
  level: InteractionLevel;
  description: string;
}

/** DDInter drug-food warning; foods sharing the same text are grouped ("spinach, rhubarb, bran"). */
export interface FoodWarning {
  ingredient: string;
  foods: string[];
  level: InteractionLevel;
  description: string;
  management: string;
}

/** GET /api/drug-warnings?registrationNumber=... */
export interface DrugWarnings {
  registrationNumber: string;
  diseases: DiseaseWarning[];
  foods: FoodWarning[];
}
