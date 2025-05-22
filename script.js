// Toggle Menu for Mobile View
document.getElementById('menu-icon').addEventListener('click', function() {
    const navLinks = document.getElementById('nav-links');
    navLinks.style.display = (navLinks.style.display === 'flex') ? 'none' : 'flex';
});
