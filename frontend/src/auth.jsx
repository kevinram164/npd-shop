import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "./api";

const AuthContext = createContext(null);
const TOKEN_KEY = "noli_token";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || "");
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!token) {
      setUser(null);
      setReady(true);
      return;
    }
    api
      .me(token)
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setToken("");
        setUser(null);
      })
      .finally(() => setReady(true));
  }, [token]);

  const value = useMemo(
    () => ({
      token,
      user,
      ready,
      isAdmin: !!user?.is_admin,
      async login(email, password) {
        const data = await api.login({ email, password });
        localStorage.setItem(TOKEN_KEY, data.access_token);
        setToken(data.access_token);
        setUser(data.user);
        return data.user;
      },
      async register(payload) {
        const data = await api.register(payload);
        localStorage.setItem(TOKEN_KEY, data.access_token);
        setToken(data.access_token);
        setUser(data.user);
        return data.user;
      },
      logout() {
        localStorage.removeItem(TOKEN_KEY);
        setToken("");
        setUser(null);
      },
    }),
    [token, user, ready]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside provider");
  return ctx;
}
