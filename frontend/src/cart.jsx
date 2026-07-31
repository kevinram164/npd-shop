import { createContext, useContext, useMemo, useReducer } from "react";

const CartContext = createContext(null);

function reducer(state, action) {
  switch (action.type) {
    case "ADD": {
      const existing = state.items.find((i) => i.product.id === action.product.id);
      if (existing) {
        return {
          items: state.items.map((i) =>
            i.product.id === action.product.id
              ? { ...i, quantity: Math.min(i.quantity + (action.qty || 1), 99) }
              : i
          ),
        };
      }
      return {
        items: [...state.items, { product: action.product, quantity: action.qty || 1 }],
      };
    }
    case "SET_QTY":
      return {
        items: state.items
          .map((i) =>
            i.product.id === action.productId
              ? { ...i, quantity: action.quantity }
              : i
          )
          .filter((i) => i.quantity > 0),
      };
    case "REMOVE":
      return { items: state.items.filter((i) => i.product.id !== action.productId) };
    case "CLEAR":
      return { items: [] };
    default:
      return state;
  }
}

export function CartProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, { items: [] });
  const value = useMemo(() => {
    const count = state.items.reduce((s, i) => s + i.quantity, 0);
    const total = state.items.reduce(
      (s, i) => s + i.product.price_vnd * i.quantity,
      0
    );
    return {
      items: state.items,
      count,
      total,
      add: (product, qty = 1) => dispatch({ type: "ADD", product, qty }),
      setQty: (productId, quantity) =>
        dispatch({ type: "SET_QTY", productId, quantity }),
      remove: (productId) => dispatch({ type: "REMOVE", productId }),
      clear: () => dispatch({ type: "CLEAR" }),
    };
  }, [state]);
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart outside provider");
  return ctx;
}
