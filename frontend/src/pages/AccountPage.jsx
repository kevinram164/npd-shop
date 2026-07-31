import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { api, formatVnd, STATUS_LABEL } from "../api";
import { useAuth } from "../auth";

export default function AccountPage() {
  const { user, token, ready, logout } = useAuth();
  const [orders, setOrders] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    api
      .myOrders(token)
      .then(setOrders)
      .catch((e) => setError(e.message));
  }, [token]);

  if (!ready) return <main className="page"><p className="muted">Đang tải…</p></main>;
  if (!user) return <Navigate to="/login" replace state={{ from: "/account" }} />;

  return (
    <main className="page">
      <div className="page-head">
        <div>
          <p className="eyebrow">Tài khoản</p>
          <h1>{user.full_name}</h1>
          <p className="muted">{user.email}</p>
        </div>
        <button type="button" className="btn btn--ghost" onClick={logout}>
          Đăng xuất
        </button>
      </div>

      <h2 className="section-title">Đơn hàng của bạn</h2>
      {error && <p className="error">{error}</p>}
      {orders.length === 0 ? (
        <p className="muted">
          Chưa có đơn nào. <Link to="/">Mua sắm ngay</Link>
        </p>
      ) : (
        <div className="order-table-wrap">
          <table className="order-table">
            <thead>
              <tr>
                <th>Mã đơn</th>
                <th>Ngày</th>
                <th>Tổng</th>
                <th>Trạng thái</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id}>
                  <td>
                    <code>{o.order_code}</code>
                  </td>
                  <td>{new Date(o.created_at).toLocaleString("vi-VN")}</td>
                  <td>{formatVnd(o.total_vnd)}</td>
                  <td>
                    <span className={`status-pill status-pill--${o.status}`}>
                      {STATUS_LABEL[o.status] || o.status}
                    </span>
                  </td>
                  <td>
                    <Link to={`/order/${o.order_code}`}>Chi tiết</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
