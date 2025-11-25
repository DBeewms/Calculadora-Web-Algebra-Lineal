/** Tailwind config for KiwiSolve Django project */
module.exports = {
  content: [
    './templates/**/*.html',
    './algebra/**/*.py',
    './core/**/*.py',
    './static/algebra/**/*.js'
  ],
  theme: {
    extend: {
      colors: {
        sky: '#7BBBC4',
        grape: '#6A1B9A',
        royal: '#7E57C2',
        violet: '#3949AB',
        savoy: '#5C6BC0'
      },
      fontFamily: {
        sans: ['Inter','system-ui','sans-serif'],
        display: ['Poppins','Inter','sans-serif']
      },
      boxShadow: {
        soft: '0 4px 12px rgba(0,0,0,.08)',
        elev: '0 8px 24px rgba(0,0,0,.08)'
      },
      borderRadius: {
        hero: '18px'
      },
      translate: {
        '0.5': '0.125rem'
      }
    }
  },
  plugins: []
};
