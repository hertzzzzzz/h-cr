// components.js
const headerHTML = `
  <nav class="bg-white border-b ...">
     <a href="/">LEVELS</a>
     <a href="leaderboard">PLAYERS</a>
  </nav>
`;

function loadComponents() {
  document.getElementById('header-container').innerHTML = headerHTML;
}