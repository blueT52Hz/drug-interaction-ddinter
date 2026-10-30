import { AlertDrugWarnings } from '../cart/interaction-alert';
import { SeverityBadge } from './severity-badge';

/**
 * Drug-disease and drug-food warnings of one drug inside the alert dialog.
 * Each item is a <details>: badge + title always visible, DDInter description (English) on expand.
 */
export function DrugWarningSections({ drug, warnings }: AlertDrugWarnings) {
  if (warnings === null) {
    return (
      <section className="dialog-section">
        <h3>Lưu ý của {drug.name}</h3>
        <p className="error-text">Không tải được lưu ý bệnh lý / thức ăn. Kiểm tra backend rồi mở lại.</p>
      </section>
    );
  }

  return (
    <>
      {warnings.diseases.length > 0 && (
        <section className="dialog-section">
          <h3>
            Lưu ý bệnh lý – {drug.name} <span className="muted">({warnings.diseases.length})</span>
          </h3>
          <ul className="warning-list">
            {warnings.diseases.map((w) => (
              <li key={`${w.ingredient}|${w.diseaseName}|${w.level}`}>
                <details>
                  <summary>
                    <SeverityBadge level={w.level} />
                    <strong>{w.diseaseName}</strong>
                    <span className="muted">({w.ingredient})</span>
                  </summary>
                  <p className="warning-text">{w.description}</p>
                </details>
              </li>
            ))}
          </ul>
        </section>
      )}
      {warnings.foods.length > 0 && (
        <section className="dialog-section">
          <h3>
            Lưu ý thức ăn – {drug.name} <span className="muted">({warnings.foods.length})</span>
          </h3>
          <ul className="warning-list">
            {warnings.foods.map((w) => (
              <li key={`${w.ingredient}|${w.level}|${w.foods.join(',')}`}>
                <details>
                  <summary>
                    <SeverityBadge level={w.level} />
                    <strong>{w.foods.join(', ')}</strong>
                    <span className="muted">({w.ingredient})</span>
                  </summary>
                  <p className="warning-text">{w.description}</p>
                  {w.management && (
                    <p className="warning-text">
                      <em>Xử trí:</em> {w.management}
                    </p>
                  )}
                </details>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
