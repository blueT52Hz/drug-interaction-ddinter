import { DrugWarnings, InteractionLevel, InteractionPair } from '../api/pos-api-types';
import { CartItem, CheckStatus } from '../cart/use-cart-with-interaction-check';
import { SEVERITY_INFO } from '../severity/interaction-severity';
import { TrashIcon } from './pos-icons';
import { SeverityBadge } from './severity-badge';

interface CartPanelProps {
  items: CartItem[];
  pairs: InteractionPair[];
  checkStatus: CheckStatus;
  errorMessage: string | null;
  /** undefined = loading, null = failed to load */
  warningsByReg: Record<string, DrugWarnings | null>;
  onShowDetails: (registrationNumber: string) => void;
  onChangeQuantity: (registrationNumber: string, delta: number) => void;
  onRemove: (registrationNumber: string) => void;
  onRetry: () => void;
}

/** Worst level + names of the other cart drugs this drug interacts with. */
function interactionSummary(reg: string, pairs: InteractionPair[], cartRegs: Set<string>) {
  let worst: InteractionLevel | null = null;
  const others = new Set<string>();
  for (const p of pairs) {
    if (!cartRegs.has(p.drug1.registrationNumber) || !cartRegs.has(p.drug2.registrationNumber)) continue;
    const other = p.drug1.registrationNumber === reg ? p.drug2 : p.drug2.registrationNumber === reg ? p.drug1 : null;
    if (!other) continue;
    others.add(other.name);
    if (worst === null || SEVERITY_INFO[p.level].rank > SEVERITY_INFO[worst].rank) worst = p.level;
  }
  return { worst, others: [...others] };
}

/** "Lưu ý: 3 bệnh lý · 1 thức ăn" button that re-opens the warning dialog for one cart drug. */
function WarningsButton({ warnings, onClick }: { warnings: DrugWarnings | null | undefined; onClick: () => void }) {
  if (warnings === undefined) return <span className="muted small-text">Đang tải lưu ý…</span>;
  if (warnings === null) {
    return (
      <button type="button" className="link-button error-text" onClick={onClick}>
        Chưa tải được lưu ý – thử lại
      </button>
    );
  }
  const parts = [
    warnings.diseases.length > 0 ? `${warnings.diseases.length} bệnh lý` : '',
    warnings.foods.length > 0 ? `${warnings.foods.length} thức ăn` : '',
  ].filter(Boolean);
  return (
    <button type="button" className="link-button" onClick={onClick}>
      {parts.length > 0 ? `Lưu ý: ${parts.join(' · ')}` : 'Xem chi tiết'}
    </button>
  );
}

/** Left area (KiotViet invoice): numbered cart lines + bottom summary card. */
export function CartPanel(props: CartPanelProps) {
  const { items, pairs, checkStatus, errorMessage, warningsByReg, onShowDetails, onChangeQuantity, onRemove, onRetry } = props;
  const cartRegs = new Set(items.map((i) => i.drug.registrationNumber));
  const totalQuantity = items.reduce((sum, i) => sum + i.quantity, 0);
  const visiblePairs = pairs.filter(
    (p) => cartRegs.has(p.drug1.registrationNumber) && cartRegs.has(p.drug2.registrationNumber),
  );

  return (
    <section className="invoice-area">
      <div className="cart-lines">
        {items.length === 0 && (
          <p className="empty-cart">Chưa có thuốc trong hóa đơn. Tìm thuốc (F3) và bấm vào thẻ thuốc bên phải để thêm.</p>
        )}
        {items.map(({ drug, quantity }, index) => {
          const { worst, others } = interactionSummary(drug.registrationNumber, pairs, cartRegs);
          return (
            <div key={drug.registrationNumber} className={`cart-line ${worst ? SEVERITY_INFO[worst].className + '-border' : ''}`}>
              <div className="cart-line-row">
                <span className="line-index">{index + 1}</span>
                <button type="button" className="icon-button" aria-label="Xóa thuốc" onClick={() => onRemove(drug.registrationNumber)}>
                  <TrashIcon />
                </button>
                <span className="line-code">{drug.registrationNumber}</span>
                <span className="line-name">{drug.name}</span>
                <div className="qty-control">
                  <button type="button" aria-label="Giảm số lượng" onClick={() => onChangeQuantity(drug.registrationNumber, -1)}>
                    −
                  </button>
                  <span className="qty-value">{quantity}</span>
                  <button type="button" aria-label="Tăng số lượng" onClick={() => onChangeQuantity(drug.registrationNumber, 1)}>
                    +
                  </button>
                </div>
              </div>
              <div className="cart-line-tags">
                {worst && <SeverityBadge level={worst} />}
                {worst && <span className="interacts-with">Tương tác với: {others.join(', ')}</span>}
                {drug.hasUnmappedIngredient && <span className="tag tag-no-data">Chưa có dữ liệu tương tác</span>}
                <WarningsButton
                  warnings={warningsByReg[drug.registrationNumber]}
                  onClick={() => onShowDetails(drug.registrationNumber)}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="summary-card">
        <div className="summary-status">
          {checkStatus === 'checking' && <span className="muted">Đang kiểm tra tương tác…</span>}
          {checkStatus === 'error' && (
            <span className="check-error">
              <span className="tag tag-error">Chưa kiểm tra được tương tác</span>
              <span className="error-text">{errorMessage}</span>
              <button type="button" className="secondary-button" onClick={onRetry}>
                Thử lại
              </button>
            </span>
          )}
          {checkStatus === 'ok' && (
            <span className="muted">
              {visiblePairs.length === 0 ? 'Không phát hiện tương tác trong dữ liệu DDInter' : `${visiblePairs.length} cặp tương tác trong hóa đơn`}
            </span>
          )}
        </div>
        <div className="summary-total">
          <span>Tổng số lượng</span>
          <strong>{totalQuantity}</strong>
        </div>
      </div>
    </section>
  );
}
