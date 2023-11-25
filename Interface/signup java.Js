const signUpForm = document.getElementById('signUpForm');
const signInForm = document.getElementById('signInForm');
const alreadyHaveAccountLink = document.getElementById('alreadyHaveAccount');
const passwordError = document.getElementById('passwordError');

alreadyHaveAccountLink.addEventListener('click', (e) => {
    e.preventDefault();
    window.location.href = 'sigin.html'; 
});

signUpForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const passwordInput = signUpForm.querySelector('input[name="password"]');
    const confirmPasswordInput = signUpForm.querySelector('input[name="confirmPassword"]');

    if (passwordInput.value !== confirmPasswordInput.value) {
        passwordError.textContent = 'Passwords not same';
        passwordError.style.color = 'red';
    } else {
        passwordError.textContent = '';
    }
});


