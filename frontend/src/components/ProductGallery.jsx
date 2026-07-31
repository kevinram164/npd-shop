import { useState } from "react";

export default function ProductGallery({ images = [], emoji = "🛍️", hue = 160, name = "" }) {
  const [active, setActive] = useState(0);
  const [failed, setFailed] = useState({});
  const list = (images || []).filter((src, i) => src && !failed[i]);
  const current = list[active] || list[0];

  function markFailed(src) {
    const idx = (images || []).indexOf(src);
    if (idx >= 0) setFailed((f) => ({ ...f, [idx]: true }));
  }

  return (
    <div className="gallery">
      <div className="gallery__main">
        {current ? (
          <img
            src={current}
            alt={`${name} — ảnh ${active + 1}`}
            loading="eager"
            onError={() => markFailed(current)}
          />
        ) : (
          <div className="product-visual product-visual--lg" style={{ "--hue": hue }}>
            <span className="product-visual__emoji">{emoji}</span>
          </div>
        )}
        {list.length > 1 && (
          <>
            <button
              type="button"
              className="gallery__nav gallery__nav--prev"
              aria-label="Ảnh trước"
              onClick={() => setActive((i) => (i - 1 + list.length) % list.length)}
            >
              ‹
            </button>
            <button
              type="button"
              className="gallery__nav gallery__nav--next"
              aria-label="Ảnh sau"
              onClick={() => setActive((i) => (i + 1) % list.length)}
            >
              ›
            </button>
          </>
        )}
      </div>
      {list.length > 0 && (
        <div className="gallery__thumbs" role="list">
          {list.map((src, i) => (
            <button
              key={src + i}
              type="button"
              role="listitem"
              className={`gallery__thumb ${i === active ? "is-active" : ""}`}
              onClick={() => setActive(i)}
            >
              <img src={src} alt="" loading="lazy" onError={() => markFailed(src)} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
