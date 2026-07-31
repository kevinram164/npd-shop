import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, formatVnd } from "../api";
import { useCart } from "../cart";
import ProductGallery from "../components/ProductGallery";

export default function ProductPage() {
  const { id } = useParams();
  const { add } = useCart();
  const [product, setProduct] = useState(null);
  const [error, setError] = useState("");
  const [added, setAdded] = useState(false);

  useEffect(() => {
    api
      .product(id)
      .then(setProduct)
      .catch((e) => setError(e.message));
  }, [id]);

  if (error) {
    return (
      <main className="page">
        <p className="error">{error}</p>
        <Link to="/">← Về trang chủ</Link>
      </main>
    );
  }

  if (!product) {
    return (
      <main className="page">
        <p className="muted">Đang tải…</p>
      </main>
    );
  }

  return (
    <main className="page product-detail">
      <ProductGallery
        images={product.images}
        emoji={product.image_emoji}
        hue={product.image_hue}
        name={product.name}
      />
      <div className="product-detail__info">
        <p className="product-tile__cat">{product.category}</p>
        <h1>{product.name}</h1>
        <p className="lede">{product.description}</p>
        <p className="price-lg">{formatVnd(product.price_vnd)}</p>
        <p className="muted">
          SKU {product.sku} · Còn {product.stock} sản phẩm · {product.images?.length || 0}{" "}
          ảnh
        </p>
        <div className="hero__actions">
          <button
            type="button"
            className="btn btn--primary"
            disabled={product.stock < 1}
            onClick={() => {
              add(product);
              setAdded(true);
            }}
          >
            {product.stock < 1 ? "Hết hàng" : "Thêm vào giỏ"}
          </button>
          {added && (
            <Link className="btn btn--text" to="/cart">
              Đi tới giỏ hàng →
            </Link>
          )}
        </div>
      </div>
    </main>
  );
}
