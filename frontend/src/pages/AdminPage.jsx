import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { api, formatVnd, STATUS_LABEL } from "../api";
import { useAuth } from "../auth";
import FinanceChart from "../components/FinanceChart";

const FILTERS = [
  { key: "", label: "Tất cả" },
  { key: "pending_payment", label: "Treo / chờ CK" },
  { key: "paid", label: "Thành công" },
  { key: "amount_mismatch", label: "Sai tiền" },
  { key: "failed", label: "Thất bại" },
  { key: "cancelled", label: "Huỷ" },
  { key: "expired", label: "Hết hạn" },
];

const GRAINS = [
  { key: "day", label: "Theo ngày", hint: "30 ngày gần nhất" },
  { key: "month", label: "Theo tháng", hint: "12 tháng" },
  { key: "year", label: "Theo năm", hint: "5 năm" },
];

export default function AdminPage() {
  const { user, token, ready, isAdmin, logout } = useAuth();
  const [stats, setStats] = useState(null);
  const [finance, setFinance] = useState(null);
  const [grain, setGrain] = useState("day");
  const [orders, setOrders] = useState([]);
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const [error, setError] = useState("");

  async function load() {
    if (!token) return;
    try {
      const [s, list, fin] = await Promise.all([
        api.adminStats(token),
        api.adminOrders(token, { status: status || undefined, q: q || undefined }),
        api.adminFinance(token, grain),
      ]);
      setStats(s);
      setOrders(list);
      setFinance(fin);
      setError("");
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    if (isAdmin) load();
  }, [token, isAdmin, status, grain]);

  if (!ready) return <main className="page"><p className="muted">Đang tải…</p></main>;
  if (!user) return <Navigate to="/login" replace state={{ from: "/admin" }} />;
  if (!isAdmin) return <Navigate to="/account" replace />;

  async function setOrderStatus(code, next) {
    await api.adminUpdateOrder(token, code, next);
    await load();
  }

  const grainMeta = GRAINS.find((g) => g.key === grain);

  return (
    <main className="page admin-page">
      <div className="page-head">
        <div>
          <p className="eyebrow">Admin portal</p>
          <h1>Theo dõi đơn hàng</h1>
        </div>
        <div className="hero__actions">
          <Link className="btn btn--ghost" to="/">
            Về shop
          </Link>
          <button type="button" className="btn btn--ghost" onClick={logout}>
            Đăng xuất
          </button>
        </div>
      </div>

      {stats && (
        <div className="stat-grid">
          <div className="stat">
            <span>Tổng đơn</span>
            <strong>{stats.total}</strong>
          </div>
          <div className="stat stat--warn">
            <span>Treo / chờ CK</span>
            <strong>{stats.pending_payment}</strong>
          </div>
          <div className="stat stat--ok">
            <span>Thành công</span>
            <strong>{stats.paid}</strong>
          </div>
          <div className="stat stat--danger">
            <span>Sai tiền</span>
            <strong>{stats.amount_mismatch}</strong>
          </div>
          <div className="stat">
            <span>Thất bại</span>
            <strong>{stats.failed}</strong>
          </div>
          <div className="stat">
            <span>Doanh thu (paid)</span>
            <strong>{formatVnd(stats.revenue_paid_vnd)}</strong>
          </div>
        </div>
      )}

      <section className="finance-dash">
        <div className="finance-dash__head">
          <div>
            <h2 className="section-title">Dashboard tài chính</h2>
            <p className="muted">
              Thu từ đơn đã thanh toán · Chi ước tính (COGS{" "}
              {finance ? Math.round(finance.cost_ratio * 100) : "—"}%) · Lãi = Thu − Chi
              {grainMeta ? ` · ${grainMeta.hint}` : ""}
            </p>
          </div>
          <div className="catalog__filters">
            {GRAINS.map((g) => (
              <button
                key={g.key}
                type="button"
                className={`chip ${grain === g.key ? "chip--active" : ""}`}
                onClick={() => setGrain(g.key)}
              >
                {g.label}
              </button>
            ))}
          </div>
        </div>

        {finance && (
          <>
            <div className="stat-grid finance-summary">
              <div className="stat stat--ok">
                <span>Tổng thu</span>
                <strong>{formatVnd(finance.inflow_vnd)}</strong>
              </div>
              <div className="stat">
                <span>Tổng chi (ước tính)</span>
                <strong>{formatVnd(finance.outflow_vnd)}</strong>
              </div>
              <div className={`stat ${finance.profit_vnd >= 0 ? "stat--ok" : "stat--danger"}`}>
                <span>{finance.profit_vnd >= 0 ? "Lãi" : "Lỗ"}</span>
                <strong>{formatVnd(finance.profit_vnd)}</strong>
              </div>
              <div className="stat stat--warn">
                <span>Chờ thu</span>
                <strong>{formatVnd(finance.pending_vnd)}</strong>
              </div>
            </div>
            <FinanceChart series={finance.series} />
          </>
        )}
      </section>

      <div className="catalog__toolbar">
        <div className="catalog__filters">
          {FILTERS.map((f) => (
            <button
              key={f.key || "all"}
              type="button"
              className={`chip ${status === f.key ? "chip--active" : ""}`}
              onClick={() => setStatus(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
        <form
          className="search"
          onSubmit={(e) => {
            e.preventDefault();
            load();
          }}
        >
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Mã đơn, CK, tên, SĐT…"
          />
          <button type="submit" className="btn btn--ghost">
            Lọc
          </button>
        </form>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="order-table-wrap">
        <table className="order-table">
          <thead>
            <tr>
              <th>Mã / CK</th>
              <th>Khách</th>
              <th>Tổng</th>
              <th>TT</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id}>
                <td>
                  <Link to={`/order/${o.order_code}`}>
                    <code>{o.order_code}</code>
                  </Link>
                  <div className="muted">{o.transfer_ref}</div>
                </td>
                <td>
                  {o.customer_name}
                  <div className="muted">{o.customer_phone}</div>
                </td>
                <td>{formatVnd(o.total_vnd)}</td>
                <td>
                  <span className={`status-pill status-pill--${o.status}`}>
                    {STATUS_LABEL[o.status] || o.status}
                  </span>
                </td>
                <td>
                  <select
                    className="admin-select"
                    value={o.status}
                    onChange={(e) => setOrderStatus(o.order_code, e.target.value)}
                  >
                    {FILTERS.filter((f) => f.key).map((f) => (
                      <option key={f.key} value={f.key}>
                        {f.label}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {orders.length === 0 && <p className="muted">Không có đơn phù hợp.</p>}
      </div>
    </main>
  );
}
