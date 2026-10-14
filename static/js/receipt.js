// Receipt page: "Print / Save as PDF" opens the browser's print dialog.
document.addEventListener("DOMContentLoaded", function () {
    const button = document.querySelector("[data-print]");
    if (button) button.addEventListener("click", function () { window.print(); });
});
