const newAccountLink = document.getElementById('newAccountLink');
const emailInput = document.getElementById('emailInput');
const icon = document.querySelector('.icon');
newAccountLink.addEventListener('click', (e) => {
    e.preventDefault();
    window.location.href = '/signup';

});




