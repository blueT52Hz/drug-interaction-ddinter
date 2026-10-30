import { InteractionPair } from '../api/pos-api-types';
import { SeverityBadge } from './severity-badge';

interface InteractionPairItemProps {
  pair: InteractionPair;
  /** expand the DDInter text right away (used for the most severe pair) */
  defaultOpen?: boolean;
}

/**
 * One drug-drug pair in the alert dialog: badge + drug/ingredient names always visible,
 * DDInter mechanism ("Cơ chế") and management ("Xử trí") text (English) on expand.
 */
export function InteractionPairItem({ pair, defaultOpen = false }: InteractionPairItemProps) {
  const title = (
    <>
      <SeverityBadge level={pair.level} />
      <span>
        <strong>{pair.drug1.name}</strong> ({pair.ingredient1}) ↔ <strong>{pair.drug2.name}</strong> ({pair.ingredient2})
      </span>
    </>
  );

  if (!pair.description && !pair.management) {
    return (
      <li>
        <div className="pair-title">{title}</div>
        <p className="warning-text muted">DDInter chưa có mô tả chi tiết cho cặp này.</p>
      </li>
    );
  }

  return (
    <li>
      <details open={defaultOpen}>
        <summary className="pair-title">{title}</summary>
        {pair.description && (
          <p className="warning-text">
            <em>Cơ chế:</em> {pair.description}
          </p>
        )}
        {pair.management && (
          <p className="warning-text">
            <em>Xử trí:</em> {pair.management}
          </p>
        )}
      </details>
    </li>
  );
}
