/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#08090c",
        surface: "#101218",
        card: "#161922",
        "card-hover": "#1c202c",
        border: "#232836",
        gold: {
          50: "#fdfbf7",
          100: "#f8f3e8",
          200: "#eee2c8",
          300: "#dfc99d",
          400: "#d4af37", // Champagne Gold Primary
          500: "#b89228",
          600: "#98721c",
          700: "#765318",
          800: "#5d4118",
          900: "#4e3517",
        },
      },
      fontFamily: {
        serif: ["Cinzel", "Playfair Display", "Georgia", "serif"],
        sans: ["Inter", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};
