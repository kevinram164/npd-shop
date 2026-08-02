import { formatVnd } from "../api";

function shortVnd(n) {
  const v = Math.abs(n);
  if (v >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}tỷ`;
  if (v >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}tr`;
  if (v >= 1_000) return `${Math.round(n / 1_000)}k`;
  return String(n);
}

/** Grouped bar chart: thu / chi / lãi — pure SVG, no chart lib. */
export default function FinanceChart({ series }) {
  const W = 720;
  const H = 280;
  const pad = { t: 24, r: 16, b: 44, l: 56 };
  const innerW = W - pad.l - pad.r;
  const innerH = H - pad.t - pad.b;
  const n = Math.max(series.length, 1);
  const groupW = innerW / n;
  const barW = Math.max(4, Math.min(14, groupW / 4));
  const maxY = Math.max(
    1,
    ...series.flatMap((p) => [p.inflow_vnd, p.outflow_vnd, Math.abs(p.profit_vnd)])
  );

  const yScale = (v) => pad.t + innerH - (v / maxY) * innerH;
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((t) => Math.round(maxY * t));

  const showEvery = n > 16 ? Math.ceil(n / 10) : n > 10 ? 2 : 1;

  return (
    <div className="finance-chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Biểu đồ thu chi lãi">
        {ticks.map((t) => {
          const y = yScale(t);
          return (
            <g key={t}>
              <line
                x1={pad.l}
                x2={W - pad.r}
                y1={y}
                y2={y}
                className="finance-chart__grid"
              />
              <text x={pad.l - 8} y={y + 4} textAnchor="end" className="finance-chart__tick">
                {shortVnd(t)}
              </text>
            </g>
          );
        })}

        {series.map((p, i) => {
          const cx = pad.l + groupW * i + groupW / 2;
          const bars = [
            { key: "in", v: p.inflow_vnd, cls: "finance-chart__bar--in" },
            { key: "out", v: p.outflow_vnd, cls: "finance-chart__bar--out" },
            { key: "profit", v: Math.max(0, p.profit_vnd), cls: "finance-chart__bar--profit" },
          ];
          return (
            <g key={p.period}>
              {bars.map((b, bi) => {
                const x = cx - (barW * 3) / 2 + bi * barW;
                const y = yScale(b.v);
                const h = Math.max(0, pad.t + innerH - y);
                return (
                  <rect
                    key={b.key}
                    x={x}
                    y={y}
                    width={barW - 1}
                    height={h}
                    className={`finance-chart__bar ${b.cls}`}
                  >
                    <title>
                      {p.label}:{" "}
                      {b.key === "in"
                        ? `Thu ${formatVnd(p.inflow_vnd)}`
                        : b.key === "out"
                          ? `Chi ${formatVnd(p.outflow_vnd)}`
                          : `Lãi ${formatVnd(p.profit_vnd)}`}
                    </title>
                  </rect>
                );
              })}
              {i % showEvery === 0 && (
                <text
                  x={cx}
                  y={H - 14}
                  textAnchor="middle"
                  className="finance-chart__label"
                >
                  {p.label}
                </text>
              )}
            </g>
          );
        })}
      </svg>
      <div className="finance-legend">
        <span className="finance-legend__item finance-legend__item--in">Thu</span>
        <span className="finance-legend__item finance-legend__item--out">Chi (ước tính)</span>
        <span className="finance-legend__item finance-legend__item--profit">Lãi</span>
      </div>
    </div>
  );
}
