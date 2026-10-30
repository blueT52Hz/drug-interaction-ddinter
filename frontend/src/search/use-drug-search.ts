import { useCallback, useEffect, useState } from 'react';
import { listDrugs, searchDrugs } from '../api/pos-api-client';
import { DrugSearchResult } from '../api/pos-api-types';

const DEBOUNCE_MS = 300;
export const MIN_QUERY_LENGTH = 2;
export const PAGE_SIZE = 18; // 3 columns x 6 rows

/**
 * Product grid data source:
 * - query shorter than 2 chars -> paged default list (featured demo drugs first), like KiotViet;
 * - otherwise -> debounced search (max 20 results, no paging).
 * Every change aborts the previous request.
 */
export function useDrugSearch() {
  const [query, setQueryState] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [results, setResults] = useState<DrugSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trimmed = query.trim();
  const isBrowsing = trimmed.length < MIN_QUERY_LENGTH;
  const searchKey = isBrowsing ? '' : trimmed; // typing a single char must not reload the default list

  const setQuery = useCallback((value: string) => {
    setQueryState(value);
    setPage(1); // a new search or going back to browsing always starts at page 1
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        if (isBrowsing) {
          const data = await listDrugs(page, PAGE_SIZE, controller.signal);
          setResults(data.items);
          setTotalPages(Math.max(1, Math.ceil(data.total / data.pageSize)));
        } else {
          setResults(await searchDrugs(searchKey, controller.signal));
          setTotalPages(1);
        }
      } catch (e) {
        if (controller.signal.aborted) return;
        setError(e instanceof Error ? e.message : 'Lỗi tải danh sách thuốc');
        setResults([]);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    // browsing/page changes load immediately; typing is debounced
    const timer = setTimeout(load, isBrowsing ? 0 : DEBOUNCE_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [searchKey, isBrowsing, page]);

  return { query, setQuery, isBrowsing, page, setPage, totalPages, results, loading, error };
}
