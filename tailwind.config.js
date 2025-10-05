// tailwind.config.js
module.exports = {
    content: [
        './templates/**/*.html', // Adjust path based on your Flask template location
        './static/**/*.js',     // Adjust path based on your Flask static JS location
    ],
    theme: {
        extend: {},
    },
    plugins: [
        require('daisyui'),
    ],
    daisyui: {
        themes: ["dracula"], // Utilise le thème Dracula
    },
};
