import { useCallback, useRef, useState } from 'react';
import { getDrugWarnings } from '../api/pos-api-client';
import { DrugWarnings } from '../api/pos-api-types';

/**
 * Per-drug cache of drug-disease / drug-food warnings.
 * `warningsByReg[reg]`: undefined = not loaded yet, null = load failed, otherwise the warnings.
 * Concurrent loads of the same drug share one request; a failed load is retried on the next call.
 */
export function useDrugWarningsCache() {
  const [warningsByReg, setWarningsByReg] = useState<Record<string, DrugWarnings | null>>({});
  const inflight = useRef(new Map<string, Promise<DrugWarnings | null>>());

  const loadWarnings = useCallback((registrationNumber: string): Promise<DrugWarnings | null> => {
    const existing = inflight.current.get(registrationNumber);
    if (existing) return existing;
    const request = getDrugWarnings(registrationNumber)
      .catch(() => null)
      .then((warnings) => {
        setWarningsByReg((prev) => ({ ...prev, [registrationNumber]: warnings }));
        if (warnings === null) inflight.current.delete(registrationNumber); // allow retry
        return warnings;
      });
    inflight.current.set(registrationNumber, request);
    return request;
  }, []);

  return { warningsByReg, loadWarnings };
}
