export interface DrugIngredient {
  name: string;
  /** DDInter drug name, null when the ingredient is not mapped to DDInter */
  ddinterDrug: string | null;
}

export interface DrugSearchResult {
  registrationNumber: string;
  name: string;
  manufacturer: string;
  packaging: string;
  ingredients: DrugIngredient[];
  /** true when at least one ingredient has no DDInter data -> UI shows "Chưa có dữ liệu tương tác" */
  hasUnmappedIngredient: boolean;
}

/** One page of the default product list (GET /api/drugs). */
export interface DrugPage {
  items: DrugSearchResult[];
  total: number;
  page: number;
  pageSize: number;
}
