// components.js
const headerHTML = `
  <nav class="bg-white border-b ...">
     <a href="index.html">LEVELS</a>
     <a href="leaderboard.html">PLAYERS</a>
  </nav>
`;

function loadComponents() {
  document.getElementById('header-container').innerHTML = headerHTML;
}