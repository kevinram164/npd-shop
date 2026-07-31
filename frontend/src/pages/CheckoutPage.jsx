import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, formatVnd } from "../api";
import { useAuth } from "../auth";
import { useCart } from "../cart";

export default function CheckoutPage() {
  const { items, total, clear } = useCart();
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    customer_name: "",
    customer_phone: "",
    customer_address: "",
    note: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!user) return;
    setForm((f) => ({
      ...f,
      customer_name: f.customer_name || user.full_name || "",
      customer_phone: f.customer_phone || user.phone || "",
    }));
  }, [user]);

  if (items.length === 0) {
    return (
      <main className="page">
        <h1>Chưa có gì để thanh toán</h1>
        <Link className="btn btn--primary" to="/">
          Về cửa hàng
        </Link>
      </main>
    );
  }

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const order = await api.createOrder(
        {
          ...form,
          items: items.map((i) => ({
            product_id: i.product.id,
            quantity: i.quantity,
          })),
        },
        token
      );
      clear();
      navigate(`/order/${order.order_code}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function field(name) {
    return {
      value: form[name],
      onChange: (e) => setForm((f) => ({ ...f, [name]: e.target.value })),
    };
  }

  return (
    <main className="page checkout">
      <div>
        <h1>Thanh toán</h1>
        <p className="lede">
          {user
            ? "Đơn sẽ gắn với tài khoản để bạn theo dõi trạng thái."
            : "Nên đăng nhập để lưu lịch sử đơn. Bạn vẫn có thể checkout khách."}
          {!user && (
            <>
              {" "}
              <Link to="/login">Đăng nhập</Link>
            </>
          )}
        </p>
        <form className="form" onSubmit={submit}>
          <label>
            Họ tên
            <input required {...field("customer_name")} placeholder="Nguyễn Văn A" />
          </label>
          <label>
            Số điện thoại
            <input required {...field("customer_phone")} placeholder="09xxxxxxxx" />
          </label>
          <label>
            Địa chỉ nhận hàng
            <textarea
              required
              rows={3}
              {...field("customer_address")}
              placeholder="Số nhà, đường, quận/huyện, tỉnh/thành"
            />
          </label>
          <label>
            Ghi chú (tuỳ chọn)
            <input {...field("note")} placeholder="Giao giờ hành chính…" />
          </label>
          {error && <p className="error">{error}</p>}
          <button className="btn btn--primary" type="submit" disabled={busy}>
            {busy ? "Đang tạo đơn…" : `Tạo đơn · ${formatVnd(total)}`}
          </button>
        </form>
      </div>
      <aside className="checkout__aside">
        <h2>Đơn của bạn</h2>
        <ul>
          {items.map(({ product, quantity }) => (
            <li key={product.id}>
              <span>
                {product.name} × {quantity}
              </span>
              <strong>{formatVnd(product.price_vnd * quantity)}</strong>
            </li>
          ))}
        </ul>
        <div className="checkout__total">
          <span>Tổng</span>
          <strong>{formatVnd(total)}</strong>
        </div>
      </aside>
    </main>
  );
}
