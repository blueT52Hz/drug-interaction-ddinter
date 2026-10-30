import { DrugPage, DrugSearchResult, DrugWarnings, InteractionPair } from './pos-api-types';

/** fetch JSON; any non-2xx response or network failure becomes an Error with a Vietnamese message. */
async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new Error('Không kết nối được máy chủ. Kiểm tra backend đã chạy chưa.');
  }
  if (!response.ok) {
    const isJson = (response.headers.get('content-type') ?? '').includes('application/json');
    if (response.status >= 500 && !isJson) {
      // Vite dev proxy answers a plain-text 500 when the backend is not running
      throw new Error('Không kết nối được máy chủ. Kiểm tra backend đã chạy chưa.');
    }
    let detail = '';
    try {
      const body = (await response.json()) as { message?: unknown };
      if (typeof body.message === 'string') detail = `: ${body.message}`;
    } catch {
      // body is not JSON - keep the status code only
    }
    throw new Error(`Máy chủ trả lỗi ${response.status}${detail}`);
  }
  return (await response.json()) as T;
}

export function searchDrugs(query: string, signal?: AbortSignal): Promise<DrugSearchResult[]> {
  return requestJson<DrugSearchResult[]>(`/api/drugs/search?q=${encodeURIComponent(query)}`, { signal });
}

export function listDrugs(page: number, pageSize: number, signal?: AbortSignal): Promise<DrugPage> {
  return requestJson<DrugPage>(`/api/drugs?page=${page}&pageSize=${pageSize}`, { signal });
}

export function getDrugWarnings(registrationNumber: string): Promise<DrugWarnings> {
  return requestJson<DrugWarnings>(`/api/drug-warnings?registrationNumber=${encodeURIComponent(registrationNumber)}`);
}

export async function checkInteractions(registrationNumbers: string[]): Promise<InteractionPair[]> {
  const body = await requestJson<{ pairs: InteractionPair[] }>('/api/interactions/check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ registrationNumbers }),
  });
  return body.pairs;
}
