document.querySelector('form').addEventListener('submit', function(e) {
    const submitButton = document.querySelector('.btn-success');
    submitButton.classList.add('loading');
    submitButton.disabled = true;
});