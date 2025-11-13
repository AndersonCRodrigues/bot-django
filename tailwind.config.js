/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',           // Templates globais
    './apps/**/templates/**/*.html',   // Templates dos apps
    './static/js/**/*.js',             // JavaScript
  ],
  theme: {
    extend: {
      colors: {
        'rpg-primary': '#4A5FBF',
        'rpg-secondary': '#6C7FD8',
        'rpg-dark': '#2D3748',
        'rpg-light': '#F7FAFC',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('daisyui'),
  ],
  daisyui: {
    themes: ["dark"],
  },
}