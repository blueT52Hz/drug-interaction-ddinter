import { DrugSearchResult } from '../api/pos-api-types';
import { ImageIcon } from './pos-icons';

interface DrugResultGridProps {
  isBrowsing: boolean;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  results: DrugSearchResult[];
  loading: boolean;
  error: string | null;
  onAddDrug: (drug: DrugSearchResult) => void;
}

const THUMB_COLORS = ['thumb-pink', 'thumb-orange', 'thumb-violet', 'thumb-blue', 'thumb-yellow', 'thumb-green'];

/** Stable placeholder colour per drug, like KiotViet's coloured image placeholders. */
const thumbColor = (reg: string): string =>
  THUMB_COLORS[[...reg].reduce((sum, ch) => sum + ch.charCodeAt(0), 0) % THUMB_COLORS.length];

const ingredientLine = (drug: DrugSearchResult): string =>
  drug.ingredients.length === 0
    ? 'Không rõ hoạt chất'
    : drug.ingredients.map((i) => i.ddinterDrug ?? i.name).join(', ');

/** Right panel: 3-column product grid (default paged list or search results); click a card to add it. */
export function DrugResultGrid(props: DrugResultGridProps) {
  const { isBrowsing, page, totalPages, onPageChange, results, loading, error, onAddDrug } = props;

  return (
    <aside className="product-panel">
      <div className="product-panel-head">
        <span className="product-panel-title">{isBrowsing ? 'Danh mục thuốc' : 'Kết quả tìm kiếm'}</span>
        <span className="muted">{loading ? 'Đang tải…' : isBrowsing ? '' : `${results.length} kết quả`}</span>
      </div>
      {error && <p className="error-text panel-message">{error}</p>}
      {!loading && !error && results.length === 0 && <p className="muted panel-message">Không tìm thấy thuốc</p>}
      <div className="product-grid">
        {results.map((drug) => (
          <button
            key={drug.registrationNumber}
            type="button"
            className="product-card"
            title={`${drug.name}\n${drug.manufacturer}\n${drug.packaging}\nHoạt chất: ${ingredientLine(drug)}`}
            onClick={() => onAddDrug(drug)}
          >
            <span className={`product-thumb ${thumbColor(drug.registrationNumber)}`}>
              <ImageIcon />
            </span>
            <span className="product-info">
              <span className="product-name">{drug.name}</span>
              <span className="product-ingredients">{ingredientLine(drug)}</span>
              <span className="product-code">{drug.registrationNumber}</span>
              {drug.hasUnmappedIngredient && <span className="tag tag-no-data">Chưa có dữ liệu tương tác</span>}
            </span>
          </button>
        ))}
      </div>
      {isBrowsing && (
        <div className="pager">
          <button type="button" aria-label="Trang trước" disabled={page <= 1 || loading} onClick={() => onPageChange(page - 1)}>
            ‹
          </button>
          <span>
            {page}/{totalPages}
          </span>
          <button
            type="button"
            aria-label="Trang sau"
            disabled={page >= totalPages || loading}
            onClick={() => onPageChange(page + 1)}
          >
            ›
          </button>
        </div>
      )}
    </aside>
  );
}
