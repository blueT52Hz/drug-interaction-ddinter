import { useEffect, useRef } from 'react';
import { useCartWithInteractionCheck } from './cart/use-cart-with-interaction-check';
import { CartPanel } from './components/cart-panel';
import { DrugResultGrid } from './components/drug-result-grid';
import { InteractionAlertDialog } from './components/interaction-alert-dialog';
import { PosTopBar } from './components/pos-top-bar';
import { useDrugSearch } from './search/use-drug-search';

/** KiotViet-style pharmacist POS: blue top bar with search, invoice on the left, drug grid on the right. */
export function App() {
  const cart = useCartWithInteractionCheck();
  const search = useDrugSearch();
  const pageRef = useRef<HTMLDivElement>(null);
  const dialogOpen = cart.alert !== null;

  // Make the page behind the dialog inert: Tab/Enter cannot reach search or cart while it is open.
  useEffect(() => {
    pageRef.current?.toggleAttribute('inert', dialogOpen);
  }, [dialogOpen]);

  return (
    <div className="app">
      <div className="app-page" ref={pageRef}>
        <PosTopBar query={search.query} onQueryChange={search.setQuery} />
        <main className="app-main">
          <CartPanel
            items={cart.items}
            pairs={cart.pairs}
            checkStatus={cart.checkStatus}
            errorMessage={cart.errorMessage}
            warningsByReg={cart.warningsByReg}
            onShowDetails={(reg) => void cart.showDrugDetails(reg)}
            onChangeQuantity={cart.changeQuantity}
            onRemove={cart.removeDrug}
            onRetry={cart.retryCheck}
          />
          <DrugResultGrid
            isBrowsing={search.isBrowsing}
            page={search.page}
            totalPages={search.totalPages}
            onPageChange={search.setPage}
            results={search.results}
            loading={search.loading}
            error={search.error}
            onAddDrug={cart.addDrug}
          />
        </main>
      </div>
      {cart.alert && <InteractionAlertDialog alert={cart.alert} onAcknowledge={cart.acknowledgeAlert} />}
    </div>
  );
}
