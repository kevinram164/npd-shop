import { Link } from "react-router-dom";
import { formatVnd } from "../api";
import { useCart } from "../cart";

export default function CartPage() {
  const { items, total, setQty, remove } = useCart();

  if (items.length === 0) {
    return (
      <main className="page">
        <h1>Giỏ hàng trống</h1>
        <p className="lede">Thêm vài món từ catalog rồi quay lại nhé.</p>
        <Link className="btn btn--primary" to="/">
          Tiếp tục mua sắm
        </Link>
      </main>
    );
  }

  return (
    <main className="page">
      <h1>Giỏ hàng</h1>
      <ul className="cart-list">
        {items.map(({ product, quantity }) => (
          <li key={product.id} className="cart-row">
            <div
              className="product-visual product-visual--sm"
              style={{ "--hue": product.image_hue }}
            >
              <span className="product-visual__emoji">{product.image_emoji}</span>
            </div>
            <div className="cart-row__meta">
              <strong>{product.name}</strong>
              <span>{formatVnd(product.price_vnd)}</span>
            </div>
            <div className="qty">
              <button
                type="button"
                onClick={() => setQty(product.id, quantity - 1)}
                aria-label="Giảm"
              >
                −
              </button>
              <span>{quantity}</span>
              <button
                type="button"
                onClick={() => setQty(product.id, quantity + 1)}
                aria-label="Tăng"
              >
                +
              </button>
            </div>
            <strong className="cart-row__sum">
              {formatVnd(product.price_vnd * quantity)}
            </strong>
            <button
              type="button"
              className="linkish"
              onClick={() => remove(product.id)}
            >
              Xóa
            </button>
          </li>
        ))}
      </ul>
      <div className="cart-summary">
        <div>
          <span className="muted">Tạm tính</span>
          <p className="price-lg">{formatVnd(total)}</p>
        </div>
        <Link className="btn btn--primary" to="/checkout">
          Thanh toán chuyển khoản
        </Link>
      </div>
    </main>
  );
}
