import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, formatVnd, STATUS_LABEL } from "../api";
import { useAuth } from "../auth";

export default function OrderPage() {
  const { code } = useParams();
  const { token } = useAuth();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState("");

  async function load() {
    try {
      const data = await api.getOrder(code, token);
      setOrder(data);
      setError("");
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    load();
    const t = window.setInterval(load, 4000);
    return () => window.clearInterval(t);
  }, [code, token]);

  function copy(text, key) {
    navigator.clipboard?.writeText(text);
    setCopied(key);
    window.setTimeout(() => setCopied(""), 1500);
  }

  if (error) {
    return (
      <main className="page">
        <p className="error">{error}</p>
        <Link to="/">← Về cửa hàng</Link>
      </main>
    );
  }

  if (!order) {
    return (
      <main className="page">
        <p className="muted">Đang tải đơn hàng…</p>
      </main>
    );
  }

  const pay = order.payment;

  return (
    <main className="page order-page">
      <p className="eyebrow">Đơn hàng</p>
      <h1>{order.order_code}</h1>
      <p className={`status-pill status-pill--${order.status}`}>
        {STATUS_LABEL[order.status] || order.status}
      </p>

      {order.status === "pending_payment" && pay && (
        <section className="pay-panel">
          <h2>Thông tin chuyển khoản</h2>
          <p className="lede">
            Chuyển đúng số tiền và nội dung để hệ thống tự khớp đơn.
          </p>
          <dl className="pay-grid">
            <div>
              <dt>Ngân hàng</dt>
              <dd>{pay.bank_name}</dd>
            </div>
            <div>
              <dt>Chủ tài khoản</dt>
              <dd>{pay.account_name}</dd>
            </div>
            <div>
              <dt>Số tài khoản</dt>
              <dd>
                <button
                  type="button"
                  className="copy-btn"
                  onClick={() => copy(pay.account_number, "acc")}
                >
                  {pay.account_number}
                  <span>{copied === "acc" ? "Đã chép" : "Chép"}</span>
                </button>
              </dd>
            </div>
            <div>
              <dt>Số tiền</dt>
              <dd>
                <button
                  type="button"
                  className="copy-btn"
                  onClick={() => copy(String(pay.amount_vnd), "amt")}
                >
                  {formatVnd(pay.amount_vnd)}
                  <span>{copied === "amt" ? "Đã chép" : "Chép"}</span>
                </button>
              </dd>
            </div>
            <div className="pay-grid__wide">
              <dt>Nội dung CK (bắt buộc đúng)</dt>
              <dd>
                <button
                  type="button"
                  className="copy-btn copy-btn--accent"
                  onClick={() => copy(pay.transfer_ref, "ref")}
                >
                  {pay.transfer_ref}
                  <span>{copied === "ref" ? "Đã chép" : "Chép mã"}</span>
                </button>
              </dd>
            </div>
          </dl>
          <p className="muted">{pay.instruction}</p>
        </section>
      )}

      {order.status === "paid" && (
        <section className="pay-panel pay-panel--ok">
          <h2>Thanh toán thành công</h2>
          <p className="lede">
            Đã nhận {formatVnd(order.paid_amount_vnd || order.total_vnd)}. Đơn
            đang được chuẩn bị giao.
          </p>
        </section>
      )}

      {order.status === "amount_mismatch" && (
        <section className="pay-panel pay-panel--warn">
          <h2>Số tiền không khớp</h2>
          <p className="lede">
            Đơn {formatVnd(order.total_vnd)} nhưng nhận{" "}
            {formatVnd(order.paid_amount_vnd || 0)}. Ops cần đối soát thủ công —
            scenario lỗi “giống đời”.
          </p>
        </section>
      )}

      <section className="order-items">
        <h2>Chi tiết</h2>
        <ul>
          {order.items.map((it) => (
            <li key={`${it.product_id}-${it.product_name}`}>
              <span>
                {it.product_name} × {it.quantity}
              </span>
              <strong>{formatVnd(it.unit_price_vnd * it.quantity)}</strong>
            </li>
          ))}
        </ul>
        <div className="checkout__total">
          <span>Tổng</span>
          <strong>{formatVnd(order.total_vnd)}</strong>
        </div>
      </section>

      <Link className="btn btn--text" to="/">
        ← Tiếp tục mua sắm
      </Link>
    </main>
  );
}
