import { InteractionLevel } from '../api/pos-api-types';

/** Vietnamese label, CSS class (colour) and rank per DDInter level. */
export const SEVERITY_INFO: Record<InteractionLevel, { label: string; className: string; rank: number }> = {
  Major: { label: 'Nghiêm trọng', className: 'severity-major', rank: 3 },
  Moderate: { label: 'Trung bình', className: 'severity-moderate', rank: 2 },
  Minor: { label: 'Nhẹ', className: 'severity-minor', rank: 1 },
  Unknown: { label: 'Chưa rõ mức độ', className: 'severity-unknown', rank: 0 },
};

/** Major/Moderate/Minor open the blocking dialog; Unknown only shows a grey label. */
export function isBlockingLevel(level: InteractionLevel): boolean {
  return level !== 'Unknown';
}
