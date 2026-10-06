// Booking page enhancements. The page works without this file:
// "Show times" reloads slots server-side and the server validates everything.
document.documentElement.classList.add("js");

document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("[data-booking-form]");
    if (!form) return;

    const showTimes = form.querySelector("[data-show-times]");
    const summary = form.querySelector("[data-summary-text]");
    const noSlots = form.querySelector("[data-no-slots]");
    const slotGrid = form.querySelector(".chip-grid--slots");
    const staleHint = form.querySelector("[data-stale-hint]");
    const dateInput = form.querySelector('input[name="date"]');
    const rupees = new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2,
        minimumFractionDigits: 0,
    });

    function refreshTimes() {
        if (showTimes) showTimes.click();
    }

    // Stylist: reload open times only when the choice was made with a pointer
    // (tap/click). Arrow keys move through radios and fire `change` on every
    // step, so a keyboard change marks the slots stale instead of reloading
    // the page mid-navigation (WCAG 3.2.2 On Input).
    let pointerChoice = false;
    form.addEventListener("pointerdown", function (event) {
        pointerChoice = Boolean(event.target.closest('label[for^="stylist-"], input[name="stylist"]'));
    });
    form.querySelectorAll('input[name="stylist"]').forEach(function (radio) {
        radio.addEventListener("change", function () {
            if (pointerChoice) {
                pointerChoice = false;
                refreshTimes();
                return;
            }
            if (slotGrid) slotGrid.setAttribute("data-stale", "");
            if (staleHint) staleHint.hidden = false;
        });
    });

    // Date: typing fires `change` as soon as the partial value is a valid
    // date (year 0002, 0020, ...). Only refresh for dates inside the bookable
    // range, and only after the user pauses.
    let dateTimer;
    if (dateInput) {
        dateInput.addEventListener("change", function () {
            clearTimeout(dateTimer);
            const value = dateInput.value;
            if (!value || (dateInput.min && value < dateInput.min) || (dateInput.max && value > dateInput.max)) {
                return;
            }
            dateTimer = setTimeout(refreshTimes, 700);
        });
    }

    function selectedServices() {
        return Array.from(form.querySelectorAll('input[name="services"]:checked'));
    }

    function formatDuration(minutes) {
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        if (!hours) return mins + " min";
        return hours + " h" + (mins ? " " + mins + " min" : "");
    }

    function addMinutes(hhmm, minutes) {
        const parts = hhmm.split(":").map(Number);
        const total = parts[0] * 60 + parts[1] + minutes;
        const h = String(Math.floor(total / 60) % 24).padStart(2, "0");
        const m = String(total % 60).padStart(2, "0");
        return h + ":" + m;
    }

    // Disable slots that can't fit the selected services before the next
    // booking or closing; re-enable ones that fit again.
    function updateSlots(minutes) {
        let open = 0;
        form.querySelectorAll('input[name="start_time"]').forEach(function (slot) {
            const reason = slot.dataset.reason;
            if (reason === "past" || reason === "booked") return;
            const tooShort = minutes > Number(slot.dataset.freeMinutes);
            slot.disabled = tooShort;
            if (tooShort && slot.checked) slot.checked = false;
            const label = form.querySelector('label[for="' + slot.id + '"] [data-slot-reason]');
            if (label) label.textContent = tooShort ? ", too short for the selected services" : "";
            if (!tooShort) open += 1;
        });
        if (noSlots) noSlots.hidden = open > 0;
    }

    function updateSummary() {
        const services = selectedServices();
        const minutes = services.reduce(function (sum, s) { return sum + Number(s.dataset.minutes); }, 0);
        const total = services.reduce(function (sum, s) { return sum + Number(s.dataset.price); }, 0);
        updateSlots(minutes);
        if (!summary) return;
        if (!services.length) {
            summary.textContent = "Choose at least one service";
            return;
        }
        const slot = form.querySelector('input[name="start_time"]:checked');
        const parts = [
            services.length + " service" + (services.length === 1 ? "" : "s"),
            formatDuration(minutes),
        ];
        if (slot) parts.push("ends " + addMinutes(slot.value, minutes));
        summary.textContent = parts.join(" · ") + " · ";
        const strong = document.createElement("strong");
        strong.textContent = rupees.format(total);
        summary.appendChild(strong);
    }

    form.addEventListener("change", function (event) {
        const name = event.target.name;
        if (name === "services" || name === "start_time") updateSummary();
    });

    // Prevent a double booking from a double click/tap on "Book appointment".
    // The Show times button submits via GET and is left alone.
    let submitting = false;
    form.addEventListener("submit", function (event) {
        const submitter = event.submitter;
        if (submitter && submitter.hasAttribute("data-show-times")) return;
        if (submitting) {
            event.preventDefault();
            return;
        }
        submitting = true;
        if (submitter) {
            submitter.setAttribute("aria-disabled", "true");
            submitter.textContent = "Booking…";
        }
    });

    // Coming back via the browser's back button restores the page from cache
    // with the button still saying "Booking…"; reset it.
    window.addEventListener("pageshow", function (event) {
        if (!event.persisted) return;
        submitting = false;
        form.querySelectorAll('.button-primary[aria-disabled="true"]').forEach(function (button) {
            button.removeAttribute("aria-disabled");
            button.textContent = "Book appointment";
        });
    });

    // Bring the error summary into view and focus after a failed submit.
    const errors = document.getElementById("error-summary");
    if (errors) errors.focus();
});
