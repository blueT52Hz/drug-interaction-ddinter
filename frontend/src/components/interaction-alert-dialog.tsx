import { useEffect, useRef } from 'react';
import { InteractionAlert } from '../cart/interaction-alert';
import { DrugWarningSections } from './drug-warning-sections';
import { InteractionPairItem } from './interaction-pair-item';
import { WarningIcon } from './pos-icons';

interface InteractionAlertDialogProps {
  alert: InteractionAlert;
  onAcknowledge: () => void;
}

/**
 * Blocking modal: no close on backdrop click or Esc - the only way out is "Đã hiểu".
 * Sections: drug-drug interactions, then drug-disease / drug-food warnings per drug.
 */
export function InteractionAlertDialog({ alert, onAcknowledge }: InteractionAlertDialogProps) {
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    buttonRef.current?.focus();
  }, []);

  return (
    <div className="dialog-backdrop">
      <div className="dialog" role="alertdialog" aria-modal="true" aria-labelledby="ddi-dialog-title">
        <h2 id="ddi-dialog-title" className="dialog-title">
          <WarningIcon /> Cảnh báo khi dùng thuốc
        </h2>
        <div className="dialog-body">
          {alert.pairs.length > 0 && (
            <section className="dialog-section">
              <h3>Tương tác thuốc – thuốc</h3>
              <ul className="warning-list">
                {alert.pairs.map((p, index) => (
                  <InteractionPairItem
                    key={`${p.drug1.registrationNumber}|${p.drug2.registrationNumber}|${p.ingredient1}|${p.ingredient2}`}
                    pair={p}
                    defaultOpen={index === 0}
                  />
                ))}
              </ul>
            </section>
          )}
          {alert.drugWarnings.map((d) => (
            <DrugWarningSections key={d.drug.registrationNumber} drug={d.drug} warnings={d.warnings} />
          ))}
        </div>
        <div className="dialog-actions">
          <button ref={buttonRef} type="button" className="primary-button" onClick={onAcknowledge}>
            Đã hiểu
          </button>
        </div>
      </div>
    </div>
  );
}
