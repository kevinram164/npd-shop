import { Link, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import { useCart } from "./cart";
import HomePage from "./pages/HomePage";
import CartPage from "./pages/CartPage";
import CheckoutPage from "./pages/CheckoutPage";
import OrderPage from "./pages/OrderPage";
import ProductPage from "./pages/ProductPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import AccountPage from "./pages/AccountPage";
import AdminPage from "./pages/AdminPage";

function Nav() {
  const { count } = useCart();
  const { user, isAdmin, logout } = useAuth();

  return (
    <header className="topbar">
      <div className="topbar__inner">
        <Link to="/" className="brand">
          <span className="brand__mark">NOLI</span>
          <span className="brand__tag">marketplace</span>
        </Link>
        <nav className="topbar__nav">
          <a href="/#catalog">Sản phẩm</a>
          <Link to="/cart" className="cart-link">
            Giỏ hàng
            {count > 0 && <span className="cart-badge">{count}</span>}
          </Link>
          {user ? (
            <>
              <Link to="/account">Đơn của tôi</Link>
              {isAdmin && <Link to="/admin">Admin</Link>}
              <button type="button" className="linkish nav-logout" onClick={logout}>
                Thoát
              </button>
            </>
          ) : (
            <>
              <Link to="/login">Đăng nhập</Link>
              <Link to="/register" className="nav-cta">
                Đăng ký
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div className="app-shell">
      <Nav />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/product/:id" element={<ProductPage />} />
        <Route path="/cart" element={<CartPage />} />
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/order/:code" element={<OrderPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/account" element={<AccountPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
      <footer className="site-footer">
        <div className="site-footer__inner">
          <strong>NOLI</strong>
          <span>Shop demo · thanh toán chuyển khoản · Kafka + banking lab</span>
        </div>
      </footer>
    </div>
  );
}
