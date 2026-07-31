import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatVnd } from "../api";
import { useCart } from "../cart";

function ProductTile({ product, onAdd }) {
  const cover = product.images?.[0];
  const [imgFailed, setImgFailed] = useState(false);
  return (
    <article className="product-tile">
      <Link to={`/product/${product.id}`} className="product-tile__media">
        {cover && !imgFailed ? (
          <div className="product-photo">
            <img
              src={cover}
              alt={product.name}
              loading="lazy"
              onError={() => setImgFailed(true)}
            />
          </div>
        ) : (
          <div className="product-visual" style={{ "--hue": product.image_hue }}>
            <span className="product-visual__emoji" aria-hidden>
              {product.image_emoji}
            </span>
            <span className="product-visual__grain" aria-hidden />
          </div>
        )}
        {product.badge && <span className="product-badge">{product.badge}</span>}
      </Link>
      <div className="product-tile__body">
        <p className="product-tile__cat">{product.category}</p>
        <Link to={`/product/${product.id}`} className="product-tile__name">
          {product.name}
        </Link>
        <div className="product-tile__row">
          <strong>{formatVnd(product.price_vnd)}</strong>
          <button type="button" className="btn btn--ghost" onClick={() => onAdd(product)}>
            Thêm
          </button>
        </div>
      </div>
    </article>
  );
}

export default function HomePage() {
  const { add } = useCart();
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [category, setCategory] = useState("");
  const [q, setQ] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState("");

  useEffect(() => {
    api.categories().then(setCategories).catch(console.error);
  }, []);

  useEffect(() => {
    setLoading(true);
    api
      .products({ category: category || undefined, q: query || undefined })
      .then(setProducts)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [category, query]);

  const totalCount = useMemo(
    () => categories.reduce((s, c) => s + c.count, 0),
    [categories]
  );

  function handleAdd(product) {
    add(product);
    setToast(`Đã thêm «${product.name}»`);
    window.setTimeout(() => setToast(""), 1800);
  }

  return (
    <main>
      <section className="hero">
        <div className="hero__atmosphere" aria-hidden />
        <div className="hero__content">
          <p className="hero__eyebrow">Chợ lifestyle Việt</p>
          <h1 className="hero__brand">NOLI</h1>
          <p className="hero__lede">
            Điện tử, thời trang, gia dụng, thực phẩm và hơn thế nữa — thanh toán
            chuyển khoản, xác nhận tự động.
          </p>
          <div className="hero__actions">
            <a className="btn btn--primary" href="#catalog">
              Khám phá {totalCount || "…"} sản phẩm
            </a>
            <Link className="btn btn--text" to="/cart">
              Xem giỏ hàng
            </Link>
          </div>
        </div>
      </section>

      <section id="catalog" className="catalog">
        <div className="catalog__toolbar">
          <div className="catalog__filters" role="tablist" aria-label="Danh mục">
            <button
              type="button"
              className={`chip ${!category ? "chip--active" : ""}`}
              onClick={() => setCategory("")}
            >
              Tất cả
            </button>
            {categories.map((c) => (
              <button
                key={c.name}
                type="button"
                className={`chip ${category === c.name ? "chip--active" : ""}`}
                onClick={() => setCategory(c.name)}
              >
                {c.name}
                <span>{c.count}</span>
              </button>
            ))}
          </div>
          <form
            className="search"
            onSubmit={(e) => {
              e.preventDefault();
              setQuery(q.trim());
            }}
          >
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Tìm sản phẩm, SKU…"
              aria-label="Tìm kiếm"
            />
            <button type="submit" className="btn btn--ghost">
              Tìm
            </button>
          </form>
        </div>

        {loading ? (
          <p className="muted">Đang tải catalog…</p>
        ) : products.length === 0 ? (
          <p className="muted">Không có sản phẩm phù hợp.</p>
        ) : (
          <div className="product-grid">
            {products.map((p) => (
              <ProductTile key={p.id} product={p} onAdd={handleAdd} />
            ))}
          </div>
        )}
      </section>

      {toast && <div className="toast">{toast}</div>}
    </main>
  );
}
