import { apiRequest } from "./auth";

export interface Page<T> {
  items: T[];
  page: number;
  size: number;
  total: number;
  pages: number;
}

export interface BaseMasterData {
  id: string;
  name: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Category extends BaseMasterData {
  description: string | null;
  parent_id: string | null;
}

export interface Unit extends BaseMasterData {
  code: string;
}

export interface Product extends BaseMasterData {
  description: string | null;
  sku: string;
  barcode: string | null;
  brand: string | null;
  category_id: string;
  category_name: string;
  unit_id: string;
  unit_code: string;
  sale_price_minor: number;
  cost_price_minor: number;
  minimum_stock: string;
}

export interface Customer extends BaseMasterData {
  kind: "individual" | "company";
  legal_name: string | null;
  masked_document: string | null;
  phone: string | null;
  email: string | null;
  address: string | null;
  notes: string | null;
}

export type MasterResource = "categories" | "units" | "products" | "customers";
export type MasterEntity = Category | Unit | Product | Customer;

export function listMasterData<T extends MasterEntity>(
  resource: MasterResource,
  search = "",
  page = 1,
  size = 10,
) {
  const query = new URLSearchParams({
    search,
    page: String(page),
    size: String(size),
  });
  return apiRequest<Page<T>>(`/${resource}?${query.toString()}`);
}

export function createMasterData<T extends MasterEntity>(
  resource: MasterResource,
  input: Record<string, unknown>,
) {
  return apiRequest<T>(`/${resource}`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateMasterData<T extends MasterEntity>(
  resource: MasterResource,
  id: string,
  input: Record<string, unknown>,
) {
  return apiRequest<T>(`/${resource}/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}
