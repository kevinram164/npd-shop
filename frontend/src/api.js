const API_BASE = import.meta.env.VITE_API_BASE || "";

async function request(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }
  const { token: _t, ...rest } = options;
  const res = await fetch(`${API_BASE}${path}`, { ...rest, headers });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text };
  }
  if (!res.ok) {
    const detail = data?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => d.msg || d).join(", ")
          : "Có lỗi xảy ra";
    throw new Error(message);
  }
  return data;
}

export const api = {
  categories: () => request("/api/categories"),
  products: ({ category, q } = {}) => {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (q) params.set("q", q);
    const qs = params.toString();
    return request(`/api/products${qs ? `?${qs}` : ""}`);
  },
  product: (id) => request(`/api/products/${id}`),
  createOrder: (body, token) =>
    request("/api/orders", { method: "POST", body: JSON.stringify(body), token }),
  getOrder: (code, token) => request(`/api/orders/${code}`, { token }),
  myOrders: (token) => request("/api/orders/mine", { token }),
  register: (body) =>
    request("/api/auth/register", { method: "POST", body: JSON.stringify(body) }),
  login: (body) =>
    request("/api/auth/login", { method: "POST", body: JSON.stringify(body) }),
  me: (token) => request("/api/auth/me", { token }),
  adminStats: (token) => request("/api/admin/stats", { token }),
  adminOrders: (token, { status, q } = {}) => {
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (q) params.set("q", q);
    const qs = params.toString();
    return request(`/api/admin/orders${qs ? `?${qs}` : ""}`, { token });
  },
  adminUpdateOrder: (token, code, status) =>
    request(`/api/admin/orders/${code}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
      token,
    }),
};

export function formatVnd(n) {
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
  }).format(n);
}

export const STATUS_LABEL = {
  pending_payment: "Chờ CK",
  paid: "Thành công",
  amount_mismatch: "Sai số tiền",
  cancelled: "Đã huỷ",
  expired: "Hết hạn",
  failed: "Thất bại",
};
