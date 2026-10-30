import { InteractionLevel } from '../api/pos-api-types';
import { SEVERITY_INFO } from '../severity/interaction-severity';

/** Coloured label: Nghiêm trọng (red) / Trung bình (orange) / Nhẹ (yellow) / Chưa rõ mức độ (grey). */
export function SeverityBadge({ level }: { level: InteractionLevel }) {
  const info = SEVERITY_INFO[level];
  return <span className={`badge ${info.className}`}>{info.label}</span>;
}
