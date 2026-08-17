import { useCallback, useEffect, useState, type FormEvent } from "react";

import type { AuthenticatedUser } from "../../lib/auth";
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

const labels: Record<MasterResource, string> = {
  products: "Produtos",
  categories: "Categorias",
  units: "Unidades",
  customers: "Clientes",
};

const emptyPage: Page<MasterEntity> = {
  items: [],
  page: 1,
  size: 10,
  total: 0,
  pages: 1,
};

export function MasterDataPanel({ user }: { user: AuthenticatedUser }) {
  const resources: MasterResource[] = user.permissions.includes(
    "catalog.manage",
  )
    ? ["products", "categories", "units", "customers"]
    : ["customers"];
  const [resource, setResource] = useState<MasterResource>(
    resources[0] ?? "customers",
  );
  const [data, setData] = useState<Page<MasterEntity>>(emptyPage);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<MasterEntity | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [categories, setCategories] = useState<Category[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);

  const refresh = useCallback(async () => {
    const result = await listMasterData(resource, search, page);
    setData(result);
  }, [page, resource, search]);

  useEffect(() => {
    void listMasterData(resource, search, page)
      .then(setData)
      .catch(() => setError("Não foi possível carregar os cadastros."));
  }, [page, resource, search]);

  useEffect(() => {
    if (!user.permissions.includes("catalog.manage")) return;
    void Promise.all([
      listMasterData<Category>("categories", "", 1, 100),
      listMasterData<Unit>("units", "", 1, 100),
    ]).then(([categoryPage, unitPage]) => {
      setCategories(categoryPage.items.filter((item) => item.active));
      setUnits(unitPage.items.filter((item) => item.active));
    });
  }, [user.permissions]);

  function switchResource(next: MasterResource) {
    setResource(next);
    setPage(1);
    setSearch("");
    setEditing(null);
    setFormOpen(false);
  }

  async function save(input: Record<string, unknown>) {
    setError("");
    try {
      if (editing) await updateMasterData(resource, editing.id, input);
      else await createMasterData(resource, input);
      setMessage(editing ? "Cadastro atualizado." : "Cadastro criado.");
      setEditing(null);
      setFormOpen(false);
      await refresh();
    } catch {
      setError(
        "Não foi possível salvar. Verifique os campos e possíveis duplicidades.",
      );
    }
  }

  async function toggle(entity: MasterEntity) {
    try {
      await updateMasterData(resource, entity.id, { active: !entity.active });
      setMessage(
        entity.active ? "Cadastro desativado." : "Cadastro reativado.",
      );
      await refresh();
    } catch {
      setError("Não foi possível alterar o status.");
    }
  }

  return (
    <section className="master-data">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Sprint 2</p>
          <h3>Cadastros fundamentais</h3>
        </div>
        <button
          onClick={() => {
            setEditing(null);
            setFormOpen(true);
          }}
          type="button"
        >
          Novo cadastro
        </button>
      </div>
      <div className="master-tabs" role="tablist">
        {resources.map((item) => (
          <button
            aria-selected={resource === item}
            key={item}
            onClick={() => switchResource(item)}
            role="tab"
            type="button"
          >
            {labels[item]}
          </button>
        ))}
      </div>
      <div className="master-toolbar">
        <input
          aria-label={`Buscar ${labels[resource]}`}
          onChange={(event) => {
            setSearch(event.target.value);
            setPage(1);
          }}
          placeholder="Buscar…"
          value={search}
        />
        <span>{data.total} registro(s)</span>
      </div>
      {error ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : null}
      {message ? <p className="success-message">{message}</p> : null}
      {formOpen ? (
        <MasterForm
          categories={categories}
          entity={editing}
          onCancel={() => {
            setFormOpen(false);
            setEditing(null);
          }}
          onSave={(input) => void save(input)}
          resource={resource}
          units={units}
        />
      ) : null}
      <div className="master-list">
        {data.items.map((entity) => (
          <article className="master-row" key={entity.id}>
            <div>
              <strong>{entityTitle(entity, resource)}</strong>
              <span>{entityDetail(entity, resource)}</span>
            </div>
            <span
              className={entity.active ? "status-active" : "status-inactive"}
            >
              {entity.active ? "Ativo" : "Inativo"}
            </span>
            <div className="row-actions">
              <button
                onClick={() => {
                  setEditing(entity);
                  setFormOpen(true);
                }}
                type="button"
              >
                Editar
              </button>
              <button onClick={() => void toggle(entity)} type="button">
                {entity.active ? "Desativar" : "Reativar"}
              </button>
            </div>
          </article>
        ))}
        {!data.items.length ? (
          <p className="empty-state">Nenhum cadastro encontrado.</p>
        ) : null}
      </div>
      <div className="pagination">
        <button
          disabled={page <= 1}
          onClick={() => setPage(page - 1)}
          type="button"
        >
          Anterior
        </button>
        <span>
          Página {data.page} de {data.pages}
        </span>
        <button
          disabled={page >= data.pages}
          onClick={() => setPage(page + 1)}
          type="button"
        >
          Próxima
        </button>
      </div>
    </section>
  );
}

function MasterForm({
  resource,
  entity,
  categories,
  units,
  onSave,
  onCancel,
}: {
  resource: MasterResource;
  entity: MasterEntity | null;
  categories: Category[];
  units: Unit[];
  onSave: (value: Record<string, unknown>) => void;
  onCancel: () => void;
}) {
  const [values, setValues] = useState<Record<string, string>>(() =>
    initialValues(resource, entity),
  );
  function field(name: string) {
    return {
      value: values[name] ?? "",
      onChange: (
        event: React.ChangeEvent<
          HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
        >,
      ) => setValues({ ...values, [name]: event.target.value }),
    };
  }
  function submit(event: FormEvent) {
    event.preventDefault();
    onSave(payloadFor(resource, values, entity));
  }
  return (
    <form className="master-form" onSubmit={submit}>
      <div className="form-heading">
        <strong>
          {entity ? "Editar" : "Novo"} {labels[resource].toLowerCase()}
        </strong>
        <button onClick={onCancel} type="button">
          Fechar
        </button>
      </div>
      {resource === "categories" ? (
        <>
          <label>
            Nome
            <input aria-label="Nome da categoria" required {...field("name")} />
          </label>
          <label>
            Descrição
            <textarea
              aria-label="Descrição da categoria"
              {...field("description")}
            />
          </label>
          <label>
            Categoria pai
            <select aria-label="Categoria pai" {...field("parent_id")}>
              <option value="">Nenhuma</option>
              {categories
                .filter((item) => item.id !== entity?.id)
                .map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
            </select>
          </label>
        </>
      ) : null}
      {resource === "units" ? (
        <>
          <label>
            Código
            <input aria-label="Código da unidade" required {...field("code")} />
          </label>
          <label>
            Nome
            <input aria-label="Nome da unidade" required {...field("name")} />
          </label>
        </>
      ) : null}
      {resource === "products" ? (
        <>
          <label>
            Nome
            <input aria-label="Nome do produto" required {...field("name")} />
          </label>
          <label>
            SKU
            <input aria-label="SKU" required {...field("sku")} />
          </label>
          <label>
            Categoria
            <select
              aria-label="Categoria do produto"
              required
              {...field("category_id")}
            >
              <option value="">Selecione</option>
              {categories.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Unidade
            <select
              aria-label="Unidade do produto"
              required
              {...field("unit_id")}
            >
              <option value="">Selecione</option>
              {units.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.code}
                </option>
              ))}
            </select>
          </label>
          <label>
            Código de barras
            <input aria-label="Código de barras" {...field("barcode")} />
          </label>
          <label>
            Marca
            <input aria-label="Marca" {...field("brand")} />
          </label>
          <label>
            Preço de venda
            <input
              aria-label="Preço de venda"
              min="0"
              step="0.01"
              type="number"
              {...field("sale_price")}
            />
          </label>
          <label>
            Preço de custo
            <input
              aria-label="Preço de custo"
              min="0"
              step="0.01"
              type="number"
              {...field("cost_price")}
            />
          </label>
          <label>
            Estoque mínimo
            <input
              aria-label="Estoque mínimo"
              min="0"
              step="0.001"
              type="number"
              {...field("minimum_stock")}
            />
          </label>
          <label className="full-field">
            Descrição
            <textarea
              aria-label="Descrição do produto"
              {...field("description")}
            />
          </label>
        </>
      ) : null}
      {resource === "customers" ? (
        <>
          <label>
            Tipo
            <select aria-label="Tipo de cliente" {...field("kind")}>
              <option value="individual">Pessoa física</option>
              <option value="company">Pessoa jurídica</option>
            </select>
          </label>
          <label>
            Nome
            <input aria-label="Nome do cliente" required {...field("name")} />
          </label>
          {values.kind === "company" ? (
            <label>
              Razão social
              <input
                aria-label="Razão social"
                required
                {...field("legal_name")}
              />
            </label>
          ) : null}
          <label>
            CPF/CNPJ
            <input
              aria-label="CPF ou CNPJ"
              placeholder={entity ? "Deixe vazio para manter" : "Opcional"}
              {...field("document")}
            />
          </label>
          <label>
            Telefone
            <input aria-label="Telefone" {...field("phone")} />
          </label>
          <label>
            E-mail
            <input
              aria-label="E-mail do cliente"
              type="email"
              {...field("email")}
            />
          </label>
          <label className="full-field">
            Endereço
            <textarea aria-label="Endereço" {...field("address")} />
          </label>
          <label className="full-field">
            Observações
            <textarea aria-label="Observações" {...field("notes")} />
          </label>
        </>
      ) : null}
      <div className="form-actions">
        <button type="submit">Salvar</button>
        <button onClick={onCancel} type="button">
          Cancelar
        </button>
      </div>
    </form>
  );
}

function initialValues(
  resource: MasterResource,
  entity: MasterEntity | null,
): Record<string, string> {
  if (!entity) return resource === "customers" ? { kind: "individual" } : {};
  const raw = entity as unknown as Record<string, unknown>;
  const values = Object.fromEntries(
    Object.entries(raw).map(([key, value]) => {
      const safeValue =
        typeof value === "string" ||
        typeof value === "number" ||
        typeof value === "boolean"
          ? String(value)
          : "";
      return [key, safeValue];
    }),
  );
  if (resource === "products") {
    const product = entity as Product;
    values.sale_price = (product.sale_price_minor / 100).toFixed(2);
    values.cost_price = (product.cost_price_minor / 100).toFixed(2);
  }
  return values;
}

function payloadFor(
  resource: MasterResource,
  values: Record<string, string>,
  entity: MasterEntity | null,
): Record<string, unknown> {
  const cleaned: Record<string, unknown> = Object.fromEntries(
    Object.entries(values).filter(([, value]) => value !== ""),
  );
  if (entity) {
    const nullableFields: Partial<Record<MasterResource, string[]>> = {
      categories: ["description", "parent_id"],
      products: ["description", "barcode", "brand"],
      customers: ["legal_name", "phone", "email", "address", "notes"],
    };
    for (const field of nullableFields[resource] ?? []) {
      if (!values[field]) cleaned[field] = null;
    }
  }
  if (resource === "products") {
    cleaned.sale_price_minor = Math.round(
      Number(values.sale_price || "0") * 100,
    );
    cleaned.cost_price_minor = Math.round(
      Number(values.cost_price || "0") * 100,
    );
    cleaned.minimum_stock = values.minimum_stock || "0";
    delete cleaned.sale_price;
    delete cleaned.cost_price;
  }
  if (resource === "customers" && entity && !values.document)
    delete cleaned.document;
  return cleaned;
}

function entityTitle(entity: MasterEntity, resource: MasterResource) {
  return resource === "units"
    ? `${(entity as Unit).code} · ${entity.name}`
    : entity.name;
}

function entityDetail(entity: MasterEntity, resource: MasterResource) {
  if (resource === "products") {
    const product = entity as Product;
    return `${product.sku} · ${product.category_name} · ${product.unit_code}`;
  }
  if (resource === "customers") {
    const customer = entity as Customer;
    return (
      [customer.masked_document, customer.email].filter(Boolean).join(" · ") ||
      "Sem documento"
    );
  }
  if (resource === "categories")
    return (entity as Category).description || "Sem descrição";
  return (entity as Unit).code;
}
