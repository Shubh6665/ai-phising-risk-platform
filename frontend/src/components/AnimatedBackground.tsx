import React from "react";

/** Pure CSS subtle background — no animations, no neon, no grid */
export const AnimatedBackground: React.FC = () => (
  <div className="fixed inset-0 -z-10 pointer-events-none" aria-hidden="true">
    <div className="absolute inset-0 bg-bg" />
    {/* Very subtle radial gradient to give depth without distracting */}
    <div
      className="absolute inset-0"
      style={{
        background:
          "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(255,255,255,0.03) 0%, transparent 100%)",
      }}
    />
  </div>
);
