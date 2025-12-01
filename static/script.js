// Basic script for modal handling and dynamic interactions

document.addEventListener('DOMContentLoaded', () => {
    // Modal handling
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.close-modal');

    closeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            modals.forEach(modal => modal.classList.remove('active'));
        });
    });

    window.addEventListener('click', (e) => {
        modals.forEach(modal => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
});

function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}
