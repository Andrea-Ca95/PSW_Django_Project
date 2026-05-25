document.addEventListener("DOMContentLoaded", function () {
    // Inizializza le piccole funzioni dinamiche dopo il caricamento della pagina.
    setMinimumDateForDateInputs();
    setupNotesCounter();
    setupConfirmForms();
});


function setMinimumDateForDateInputs() {
    // Impedisce graficamente di scegliere date precedenti a oggi.
    const dateInputs = document.querySelectorAll('input[type="date"]');

    if (!dateInputs.length) {
        return;
    }

    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, "0");
    const day = String(today.getDate()).padStart(2, "0");
    const todayValue = `${year}-${month}-${day}`;

    dateInputs.forEach(function (input) {
        input.min = todayValue;
    });
}


function setupNotesCounter() {
    // Aggiunge un contatore caratteri sotto il campo note, se presente.
    const notesField = document.querySelector("textarea[name='notes']");

    if (!notesField) {
        return;
    }

    const maxLength = notesField.getAttribute("maxlength") || 500;
    const counter = document.createElement("small");

    counter.className = "char-counter";
    notesField.insertAdjacentElement("afterend", counter);

    function updateCounter() {
        counter.textContent = `${notesField.value.length}/${maxLength} caratteri`;
    }

    notesField.addEventListener("input", updateCounter);
    updateCounter();
}


function setupConfirmForms() {
    // Mostra una conferma prima delle azioni che modificano un appuntamento.
    const forms = document.querySelectorAll("form[data-confirm]");

    forms.forEach(function (form) {
        form.addEventListener("submit", function (event) {
            const message = form.getAttribute("data-confirm");

            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });
}