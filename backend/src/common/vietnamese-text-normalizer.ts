/**
 * Normalize text for accent-insensitive search:
 * "Thuốc Đau Đầu" -> "thuoc dau dau".
 * Shared by the import script (builds drugs.search_text) and DrugsService (normalizes the query).
 */
export function normalizeForSearch(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '') // strip combining diacritics
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim();
}
