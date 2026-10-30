import { DrugRef, DrugWarnings, InteractionPair } from '../api/pos-api-types';
import { SEVERITY_INFO } from '../severity/interaction-severity';

/** Drug-disease / drug-food warnings of one drug shown in the dialog; null = failed to load. */
export interface AlertDrugWarnings {
  drug: DrugRef;
  warnings: DrugWarnings | null;
}

/** Content of the blocking dialog: drug-drug pairs + per-drug disease/food warnings. */
export interface InteractionAlert {
  pairs: InteractionPair[];
  drugWarnings: AlertDrugWarnings[];
}

const pairKey = (p: InteractionPair): string =>
  `${p.drug1.registrationNumber}|${p.drug2.registrationNumber}|${p.ingredient1}|${p.ingredient2}`;

export const hasWarnings = (w: DrugWarnings): boolean => w.diseases.length + w.foods.length > 0;

/** Show a drug in the dialog when it has warnings or when loading them failed (never hide a failure). */
export const isWorthShowing = (d: AlertDrugWarnings): boolean => d.warnings === null || hasWarnings(d.warnings);

export const isAlertEmpty = (a: InteractionAlert): boolean => a.pairs.length === 0 && a.drugWarnings.length === 0;

/**
 * Union of the open alert and a new one: an alert that was not acknowledged yet must never disappear.
 * Pairs are deduplicated and sorted most severe first; drug warnings are deduplicated per drug.
 */
export function mergeAlerts(prev: InteractionAlert | null, next: InteractionAlert): InteractionAlert {
  const pairs = new Map((prev?.pairs ?? []).map((p) => [pairKey(p), p]));
  for (const p of next.pairs) pairs.set(pairKey(p), p);
  const drugs = new Map((prev?.drugWarnings ?? []).map((d) => [d.drug.registrationNumber, d]));
  for (const d of next.drugWarnings) drugs.set(d.drug.registrationNumber, d);
  return {
    pairs: [...pairs.values()].sort((a, b) => SEVERITY_INFO[b.level].rank - SEVERITY_INFO[a.level].rank),
    drugWarnings: [...drugs.values()],
  };
}
