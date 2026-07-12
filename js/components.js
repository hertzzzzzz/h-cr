// components.js
const headerHTML = `
  <nav class="bg-white border-b ...">
     <a href="index.html">TOP-100</a>
     <a href="leaderboard.html">leaderboard</a>
  </nav>
`;

function loadComponents() {
  document.getElementById('header-container').innerHTML = headerHTML;
}