import { useCallback, useRef, useState } from 'react';
import { checkInteractions } from '../api/pos-api-client';
import { DrugSearchResult, InteractionPair } from '../api/pos-api-types';
import { isBlockingLevel } from '../severity/interaction-severity';
import { InteractionAlert, isAlertEmpty, isWorthShowing, mergeAlerts } from './interaction-alert';
import { useDrugWarningsCache } from './use-drug-warnings-cache';

export interface CartItem {
  drug: DrugSearchResult;
  quantity: number;
}

export type CheckStatus = 'idle' | 'checking' | 'ok' | 'error';

/**
 * Cart state + checks after every cart change.
 * - Newly added drugs are "pending": the next successful check opens the blocking dialog with their
 *   Major/Moderate/Minor drug-drug pairs and their drug-disease / drug-food warnings
 *   (kept across failed checks so "Thử lại" can still alert).
 * - Each check has an incrementing id; only the latest response is applied (rapid adds never race).
 */
export function useCartWithInteractionCheck() {
  const [items, setItems] = useState<CartItem[]>([]);
  const [pairs, setPairs] = useState<InteractionPair[]>([]);
  const [checkStatus, setCheckStatus] = useState<CheckStatus>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [alert, setAlert] = useState<InteractionAlert | null>(null);
  const { warningsByReg, loadWarnings } = useDrugWarningsCache();

  const itemsRef = useRef<CartItem[]>([]); // latest cart, readable from async callbacks
  const pairsRef = useRef<InteractionPair[]>([]);
  const pendingAlertRegs = useRef(new Set<string>());
  const latestRequestId = useRef(0);

  const commitItems = useCallback((next: CartItem[]) => {
    itemsRef.current = next;
    setItems(next);
  }, []);

  const drugRef = (reg: string) => {
    const item = itemsRef.current.find((i) => i.drug.registrationNumber === reg);
    return item ? { registrationNumber: reg, name: item.drug.name } : null;
  };

  const openAlert = useCallback((next: InteractionAlert) => {
    if (!isAlertEmpty(next)) setAlert((prev) => mergeAlerts(prev, next));
  }, []);

  const runCheck = useCallback(
    async (cart: CartItem[]) => {
      const requestId = ++latestRequestId.current;
      if (cart.length === 0) {
        pendingAlertRegs.current.clear();
        pairsRef.current = [];
        setPairs([]);
        setCheckStatus('idle');
        setErrorMessage(null);
        return;
      }
      setCheckStatus('checking');
      try {
        const regs = cart.map((item) => item.drug.registrationNumber);
        const pendingRegs = [...pendingAlertRegs.current];
        const [result, warnings] = await Promise.all([checkInteractions(regs), Promise.all(pendingRegs.map(loadWarnings))]);
        if (requestId !== latestRequestId.current) return; // a newer cart is being checked
        pendingRegs.forEach((reg) => pendingAlertRegs.current.delete(reg));
        pairsRef.current = result;
        setPairs(result);
        setCheckStatus('ok');
        setErrorMessage(null);
        const pending = new Set(pendingRegs);
        openAlert({
          pairs: result.filter(
            (p) => isBlockingLevel(p.level) && (pending.has(p.drug1.registrationNumber) || pending.has(p.drug2.registrationNumber)),
          ),
          drugWarnings: pendingRegs
            .flatMap((reg, i) => {
              const drug = drugRef(reg); // skip drugs removed from the cart meanwhile
              return drug ? [{ drug, warnings: warnings[i] }] : [];
            })
            .filter(isWorthShowing),
        });
      } catch (error) {
        if (requestId !== latestRequestId.current) return;
        setCheckStatus('error');
        setErrorMessage(error instanceof Error ? error.message : 'Lỗi không xác định');
      }
    },
    [loadWarnings, openAlert],
  );

  const addDrug = useCallback(
    (drug: DrugSearchResult) => {
      const current = itemsRef.current;
      const reg = drug.registrationNumber;
      if (current.some((item) => item.drug.registrationNumber === reg)) {
        // already in cart: only bump quantity, no re-check
        commitItems(current.map((item) => (item.drug.registrationNumber === reg ? { ...item, quantity: item.quantity + 1 } : item)));
        return;
      }
      const next = [...current, { drug, quantity: 1 }];
      commitItems(next);
      pendingAlertRegs.current.add(reg);
      void runCheck(next);
    },
    [commitItems, runCheck],
  );

  const changeQuantity = useCallback(
    (registrationNumber: string, delta: number) => {
      commitItems(
        itemsRef.current.map((item) =>
          item.drug.registrationNumber === registrationNumber ? { ...item, quantity: Math.max(1, item.quantity + delta) } : item,
        ),
      );
    },
    [commitItems],
  );

  const removeDrug = useCallback(
    (registrationNumber: string) => {
      const next = itemsRef.current.filter((item) => item.drug.registrationNumber !== registrationNumber);
      commitItems(next);
      pendingAlertRegs.current.delete(registrationNumber);
      void runCheck(next); // recompute labels; dialog only for drugs still pending
    },
    [commitItems, runCheck],
  );

  /** Re-open the dialog for one cart drug: all its pairs (any level) + its disease/food warnings. */
  const showDrugDetails = useCallback(
    async (registrationNumber: string) => {
      const drug = drugRef(registrationNumber);
      if (!drug) return;
      const warnings = await loadWarnings(registrationNumber);
      openAlert({
        pairs: pairsRef.current.filter(
          (p) => p.drug1.registrationNumber === registrationNumber || p.drug2.registrationNumber === registrationNumber,
        ),
        drugWarnings: [{ drug, warnings }].filter(isWorthShowing),
      });
    },
    [loadWarnings, openAlert],
  );

  const retryCheck = useCallback(() => void runCheck(itemsRef.current), [runCheck]);
  const acknowledgeAlert = useCallback(() => setAlert(null), []);

  return {
    items, pairs, checkStatus, errorMessage, alert, warningsByReg,
    addDrug, changeQuantity, removeDrug, retryCheck, acknowledgeAlert, showDrugDetails,
  };
}
