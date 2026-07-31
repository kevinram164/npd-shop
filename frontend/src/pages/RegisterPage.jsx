import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    email: "",
    password: "",
    full_name: "",
    phone: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function field(name) {
    return {
      value: form[name],
      onChange: (e) => setForm((f) => ({ ...f, [name]: e.target.value })),
    };
  }

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await register(form);
      navigate("/account");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page auth-page">
      <h1>Đăng ký</h1>
      <p className="lede">Tạo tài khoản để lưu và theo dõi đơn hàng.</p>
      <form className="form" onSubmit={submit}>
        <label>
          Họ tên
          <input required {...field("full_name")} />
        </label>
        <label>
          Email
          <input type="email" required {...field("email")} />
        </label>
        <label>
          Số điện thoại
          <input {...field("phone")} placeholder="09xxxxxxxx" />
        </label>
        <label>
          Mật khẩu (≥ 6 ký tự)
          <input type="password" required minLength={6} {...field("password")} />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="btn btn--primary" disabled={busy}>
          {busy ? "Đang tạo…" : "Tạo tài khoản"}
        </button>
      </form>
      <p className="muted">
        Đã có tài khoản? <Link to="/login">Đăng nhập</Link>
      </p>
    </main>
  );
}
