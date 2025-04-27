module.exports = {
  content: [
    "./main_site/templates/**/*.html",
    "./main_site/components/**/*.py",
  ],
  theme: {
    extend: {},
    colors: {},
  },
  plugins: [],
  safelist: [
    "from-gold-light",
    "to-gold-dark",
    "from-silver-light",
    "to-silver-dark",
    "from-bronze-light",
    "to-bronze-dark",
  ],
};
