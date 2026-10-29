/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        void: "#04060f",
        "glass-base": "rgba(13, 17, 35, 0.65)",
        slate: {
          850: "#151e2e",
          925: "#0c1220",
          950: "#0b0f19",
          975: "#070a14",
        },
        cyan: {
          350: "#67e8f9",
        },
        violet: {
          350: "#c4b5fd",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out forwards",
        "fade-up": "fadeUp 0.6s ease-out forwards",
        "slide-in-right": "slideInRight 0.4s ease-out forwards",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "gradient-shift": "gradientShift 6s ease infinite",
        "float": "float 6s ease-in-out infinite",
        "scan": "scan 3s linear infinite",
        "data-pulse": "dataPulse 2s ease-in-out infinite",
        "border-glow": "borderGlow 2s ease-in-out infinite",
        "spin-slow": "spin 4s linear infinite",
        "orb-1": "orbFloat1 12s ease-in-out infinite",
        "orb-2": "orbFloat2 15s ease-in-out infinite",
        "orb-3": "orbFloat3 18s ease-in-out infinite",
        "typewriter": "typewriter 0.05s steps(1) forwards",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        fadeUp: {
          from: { opacity: "0", transform: "translateY(16px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          from: { opacity: "0", transform: "translateX(20px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        gradientShift: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-12px)" },
        },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
        dataPulse: {
          "0%, 100%": { opacity: "0.5", transform: "scale(0.95)" },
          "50%": { opacity: "1", transform: "scale(1.05)" },
        },
        borderGlow: {
          "0%, 100%": { boxShadow: "0 0 5px rgba(34,211,238,0.2)" },
          "50%": { boxShadow: "0 0 20px rgba(34,211,238,0.4), 0 0 40px rgba(139,92,246,0.2)" },
        },
        orbFloat1: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%": { transform: "translate(30px, -40px) scale(1.05)" },
          "66%": { transform: "translate(-20px, 20px) scale(0.95)" },
        },
        orbFloat2: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "40%": { transform: "translate(-35px, 30px) scale(1.08)" },
          "70%": { transform: "translate(25px, -20px) scale(0.92)" },
        },
        orbFloat3: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "50%": { transform: "translate(20px, 40px) scale(1.04)" },
        },
      },
      backgroundImage: {
        "grid-pattern": "linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)",
        "radial-glow": "radial-gradient(ellipse at 50% 50%, rgba(34,211,238,0.12) 0%, transparent 70%)",
      },
      backgroundSize: {
        "grid": "40px 40px",
      },
      backdropBlur: {
        "xs": "4px",
      },
      boxShadow: {
        "glass": "0 8px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06)",
        "glass-sm": "0 4px 16px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)",
        "neon-cyan": "0 0 20px rgba(34,211,238,0.3), 0 0 60px rgba(34,211,238,0.1)",
        "neon-violet": "0 0 20px rgba(139,92,246,0.3), 0 0 60px rgba(139,92,246,0.1)",
        "neon-red": "0 0 20px rgba(248,113,113,0.3), 0 0 60px rgba(248,113,113,0.1)",
        "neon-emerald": "0 0 20px rgba(52,211,153,0.3), 0 0 60px rgba(52,211,153,0.1)",
      },
    },
  },
  plugins: [],
};
