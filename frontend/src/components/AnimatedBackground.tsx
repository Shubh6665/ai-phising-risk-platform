import React from "react";

/** Minimal, refined background: subtle dark canvas with fine engineering grid */
export const AnimatedBackground: React.FC = () => {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none" aria-hidden="true">
      {/* Base deep dark background */}
      <div className="absolute inset-0 bg-[#0b0f19]" />

      {/* Fine subtle engineering grid */}
      <div
        className="absolute inset-0 opacity-[0.18]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      {/* Very subtle top vignette */}
      <div
        className="absolute inset-x-0 top-0 h-48 pointer-events-none"
        style={{
          background: "linear-gradient(to bottom, rgba(15, 23, 42, 0.4), transparent)",
        }}
      />
    </div>
  );
};
