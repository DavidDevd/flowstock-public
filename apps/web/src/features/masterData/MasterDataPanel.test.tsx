import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  createMasterData,
  listMasterData,
  updateMasterData,
  type Category,
  type Customer,
  type MasterEntity,
  type MasterResource,
  type Page,
  type Product,
  type Unit,
} from "../../lib/masterData";
import { MasterDataPanel } from "./MasterDataPanel";

vi.mock("../../lib/masterData", () => ({
  createMasterData: vi.fn(),
  listMasterData: vi.fn(),
  updateMasterData: vi.fn(),
}));

const now = "2026-07-30T12:00:00Z";
const category: Category = {
  id: "category-1",
  name: "Bebidas",
  description: "Bebidas em geral",
  parent_id: null,
  active: true,
  created_at: now,
  updated_at: now,
};
const unit: Unit = {
  id: "unit-1",
  code: "UN",
  name: "Unidade",
  active: true,
  created_at: now,
  updated_at: now,
};
const product: Product = {
  id: "product-1",
  name: "Água",
  description: "Sem gás",
  sku: "AGUA-1",
  barcode: "7891234567890",
  brand: "Flow",
  category_id: category.id,
  category_name: category.name,
  unit_id: unit.id,
  unit_code: unit.code,
  sale_price_minor: 1234,
  cost_price_minor: 567,
  minimum_stock: "2.500",
  active: true,
  created_at: now,
  updated_at: now,
};
const customer: Customer = {
  id: "customer-1",
  kind: "individual",
  name: "Maria",
  legal_name: null,
  masked_document: "***.***.***-25",
  phone: "71999999999",
  email: "maria@example.com",
  address: "Salvador",
  notes: null,
  active: true,
  created_at: now,
  updated_at: now,
};

const admin = {
  id: "admin-1",
  email: "admin@example.com",
  name: "Admin",
  role: "administrator",
  permissions: ["catalog.manage", "customers.manage"],
  must_change_password: false,
  active: true,
};
const cashier = {
  ...admin,
  id: "cashier-1",
  role: "cashier",
  permissions: ["customers.manage"],
};

function page<T extends MasterEntity>(
  items: T[],
  currentPage = 1,
  pages = 1,
): Page<T> {
  return {
    items,
    page: currentPage,
    size: 10,
    total: items.length,
    pages,
  };
}

function mockLists() {
  vi.mocked(listMasterData).mockImplementation(
    (resource: MasterResource, _search?: string, currentPage = 1) => {
      const values: Record<MasterResource, MasterEntity[]> = {
        categories: [category],
        units: [unit],
        products: [product],
        customers: [customer],
      };
      return Promise.resolve(
        page(values[resource], currentPage, resource === "products" ? 2 : 1),
      );
    },
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockLists();
  vi.mocked(createMasterData).mockResolvedValue(category);
  vi.mocked(updateMasterData).mockImplementation((_resource, _id, input) =>
    Promise.resolve({ ...product, ...input }),
  );
});

describe("MasterDataPanel", () => {
  it("edits prices, clears optional product fields and changes status", async () => {
    render(<MasterDataPanel user={admin} />);
    expect(
      await screen.findByText("AGUA-1 · Bebidas · UN"),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Buscar Produtos"), {
      target: { value: "água" },
    });
    await waitFor(() =>
      expect(listMasterData).toHaveBeenCalledWith("products", "água", 1),
    );
    fireEvent.click(screen.getByRole("button", { name: "Próxima" }));
    await waitFor(() =>
      expect(listMasterData).toHaveBeenCalledWith("products", "água", 2),
    );
    fireEvent.click(screen.getByRole("button", { name: "Anterior" }));

    fireEvent.click(screen.getByRole("button", { name: "Editar" }));
    expect(screen.getByLabelText("Preço de venda")).toHaveValue(12.34);
    expect(screen.getByLabelText("Preço de custo")).toHaveValue(5.67);
    fireEvent.change(screen.getByLabelText("Descrição do produto"), {
      target: { value: "" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
    await waitFor(() =>
      expect(updateMasterData).toHaveBeenCalledWith(
        "products",
        product.id,
        expect.objectContaining({
          sale_price_minor: 1234,
          cost_price_minor: 567,
          minimum_stock: "2.500",
          description: null,
        }),
      ),
    );
    expect(await screen.findByText("Cadastro atualizado.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Desativar" }));
    await waitFor(() =>
      expect(updateMasterData).toHaveBeenCalledWith("products", product.id, {
        active: false,
      }),
    );
    expect(await screen.findByText("Cadastro desativado.")).toBeInTheDocument();
  });

  it("creates a child category and exercises cancellation", async () => {
    render(<MasterDataPanel user={admin} />);
    fireEvent.click(await screen.findByRole("tab", { name: "Categorias" }));
    expect(await screen.findByText("Bebidas em geral")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Novo cadastro" }));
    fireEvent.change(screen.getByLabelText("Nome da categoria"), {
      target: { value: "Sucos" },
    });
    fireEvent.change(screen.getByLabelText("Descrição da categoria"), {
      target: { value: "Naturais" },
    });
    fireEvent.change(screen.getByLabelText("Categoria pai"), {
      target: { value: category.id },
    });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
    await waitFor(() =>
      expect(createMasterData).toHaveBeenCalledWith("categories", {
        name: "Sucos",
        description: "Naturais",
        parent_id: category.id,
      }),
    );
    expect(await screen.findByText("Cadastro criado.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Novo cadastro" }));
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(
      screen.queryByLabelText("Nome da categoria"),
    ).not.toBeInTheDocument();
  });

  it("creates a unit and displays its specialized title", async () => {
    render(<MasterDataPanel user={admin} />);
    fireEvent.click(await screen.findByRole("tab", { name: "Unidades" }));
    expect(await screen.findByText("UN · Unidade")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Novo cadastro" }));
    fireEvent.change(screen.getByLabelText("Código da unidade"), {
      target: { value: "FD" },
    });
    fireEvent.change(screen.getByLabelText("Nome da unidade"), {
      target: { value: "Fardo" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
    await waitFor(() =>
      expect(createMasterData).toHaveBeenCalledWith("units", {
        code: "FD",
        name: "Fardo",
      }),
    );
  });

  it("limits a cashier to customers and handles save and status failures", async () => {
    render(<MasterDataPanel user={cashier} />);
    expect(
      await screen.findByText("***.***.***-25 · maria@example.com"),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("tab", { name: "Produtos" }),
    ).not.toBeInTheDocument();
    expect(listMasterData).not.toHaveBeenCalledWith("categories", "", 1, 100);

    vi.mocked(createMasterData).mockRejectedValueOnce(new Error("conflict"));
    fireEvent.click(screen.getByRole("button", { name: "Novo cadastro" }));
    fireEvent.change(screen.getByLabelText("Tipo de cliente"), {
      target: { value: "company" },
    });
    fireEvent.change(screen.getByLabelText("Nome do cliente"), {
      target: { value: "Flow Cliente" },
    });
    fireEvent.change(screen.getByLabelText("Razão social"), {
      target: { value: "Flow Cliente Ltda." },
    });
    fireEvent.change(screen.getByLabelText("CPF ou CNPJ"), {
      target: { value: "04.252.011/0001-10" },
    });
    fireEvent.change(screen.getByLabelText("Telefone"), {
      target: { value: "7133334444" },
    });
    fireEvent.change(screen.getByLabelText("E-mail do cliente"), {
      target: { value: "cliente@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Endereço"), {
      target: { value: "Bahia" },
    });
    fireEvent.change(screen.getByLabelText("Observações"), {
      target: { value: "Atacado" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Não foi possível salvar",
    );

    vi.mocked(updateMasterData).mockRejectedValueOnce(new Error("failure"));
    fireEvent.click(screen.getByRole("button", { name: "Desativar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Não foi possível alterar o status.",
    );
  });

  it("reports a safe initial loading failure", async () => {
    vi.mocked(listMasterData).mockRejectedValue(new Error("sensitive"));
    render(<MasterDataPanel user={cashier} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Não foi possível carregar os cadastros.",
    );
    expect(screen.getByText("Nenhum cadastro encontrado.")).toBeInTheDocument();
  });
});
