export type InteractionLevel = 'Major' | 'Moderate' | 'Minor' | 'Unknown';

export interface DrugRef {
  registrationNumber: string;
  name: string;
}

/** One interacting ingredient pair between two different drugs in the cart. */
export interface InteractionPair {
  /** the drug that appears earlier in the request array */
  drug1: DrugRef;
  drug2: DrugRef;
  /** DDInter drug name of the interacting ingredient of drug1 */
  ingredient1: string;
  ingredient2: string;
  level: InteractionLevel;
  /** DDInter mechanism/effect text (English), '' when DDInter has none */
  description: string;
  /** DDInter management advice (English), '' when DDInter has none */
  management: string;
}

export const SEVERITY_RANK: Record<InteractionLevel, number> = { Major: 3, Moderate: 2, Minor: 1, Unknown: 0 };

/** Any level value outside the known set is treated as Unknown. */
export function toInteractionLevel(value: string): InteractionLevel {
  return value === 'Major' || value === 'Moderate' || value === 'Minor' ? value : 'Unknown';
}
