// Booking wizard. The page works without this file: every step is visible,
// "Show times" reloads slots server-side and the server validates everything.
// With JS the form becomes one step at a time, with a progress bar and
// time picker; the same fields are still submitted in a single POST.
document.documentElement.classList.add("js");

document.addEventListener("DOMContentLoaded", function () {
    try {
        initWizard();
    } catch (error) {
        // Never leave the page blank: drop back to the plain form.
        document.documentElement.classList.remove("js");
        document.documentElement.classList.add("wizard-ready");
        if (window.console) console.error(error);
    }
});

function initWizard() {
    const form = document.querySelector("[data-booking-form]");
    if (!form) return;

    const allSteps = Array.from(form.querySelectorAll(".wizard-step"));
    const summary = form.querySelector("[data-summary-text]");
    const backButton = form.querySelector('[data-nav="back"]');
    const nextButton = form.querySelector('[data-nav="next"]');
    const submitButton = form.querySelector("[data-submit]");
    const progress = document.querySelector("[data-progress]");
    const dateInput = form.querySelector('input[name="date"]');
    const slotsUrl = form.dataset.slotsUrl;
    const openTime = form.dataset.open;
    const closeTime = form.dataset.close;
    const rupees = new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2,
        minimumFractionDigits: 0,
    });
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

    // ---- Helpers ----------------------------------------------------------

    function stepId(el) { return el.dataset.step; }
    function isGuest() {
        const checked = form.querySelector('input[name="booked_for_guest"]:checked');
        return Boolean(checked && checked.value === "true");
    }
    function activeSteps() {
        return allSteps.filter(function (el) { return stepId(el) !== "guest" || isGuest(); });
    }
    function selectedServices() {
        return Array.from(form.querySelectorAll('input[name="services"]:checked'));
    }
    function totals() {
        const services = selectedServices();
        return {
            services: services,
            minutes: services.reduce(function (sum, s) { return sum + Number(s.dataset.minutes); }, 0),
            price: services.reduce(function (sum, s) { return sum + Number(s.dataset.price); }, 0),
        };
    }
    function formatDuration(minutes) {
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        if (!hours) return mins + " min";
        return hours + " h" + (mins ? " " + mins + " min" : "");
    }
    function toMinutes(hhmm) {
        const parts = hhmm.split(":").map(Number);
        return parts[0] * 60 + parts[1];
    }
    function format12(totalMinutes) {
        const h24 = Math.floor(totalMinutes / 60) % 24;
        const m = totalMinutes % 60;
        const suffix = h24 >= 12 ? "PM" : "AM";
        return (h24 % 12 || 12) + ":" + String(m).padStart(2, "0") + " " + suffix;
    }
    function clearJsErrors(scope) {
        scope.querySelectorAll("[data-js-error]").forEach(function (el) { el.remove(); });
        scope.querySelectorAll('[aria-invalid="true"][data-js-invalid]').forEach(function (el) {
            el.removeAttribute("aria-invalid");
            el.removeAttribute("data-js-invalid");
        });
    }
    function fieldError(input, message) {
        const error = document.createElement("p");
        error.className = "form-error";
        error.id = input.id + "-js-error";
        error.setAttribute("data-js-error", "");
        error.textContent = message;
        input.setAttribute("aria-invalid", "true");
        input.setAttribute("data-js-invalid", "");
        input.setAttribute("aria-describedby", error.id);
        input.insertAdjacentElement("afterend", error);
    }
    function stepError(step, message) {
        const error = document.createElement("p");
        error.className = "form-error";
        error.setAttribute("data-js-error", "");
        error.setAttribute("role", "alert");
        error.textContent = message;
        const legend = step.querySelector("legend");
        legend.insertAdjacentElement("afterend", error);
    }

    // ---- Services: category cards reveal their service chips -------------

    const categoryToggles = Array.from(form.querySelectorAll("[data-category-toggle]"));
    const emptyServicesHint = form.querySelector("[data-services-empty]");

    function groupFor(id) { return form.querySelector('[data-category-group="' + id + '"]'); }

    function syncCategories() {
        let any = false;
        categoryToggles.forEach(function (toggle) {
            const id = toggle.dataset.categoryToggle;
            const group = groupFor(id);
            if (group) group.hidden = !toggle.checked;
            if (toggle.checked) any = true;
            // How many services are chosen in this area, even while it's closed.
            const chosen = group ? group.querySelectorAll('input[name="services"]:checked').length : 0;
            const badge = form.querySelector('[data-category-count="' + id + '"]');
            if (badge) {
                badge.hidden = chosen === 0;
                badge.textContent = String(chosen);
                badge.setAttribute("aria-label", chosen + " selected");
            }
        });
        if (emptyServicesHint) emptyServicesHint.hidden = any;
    }

    categoryToggles.forEach(function (toggle) {
        const group = groupFor(toggle.dataset.categoryToggle);
        if (group && group.querySelector('input[name="services"]:checked')) toggle.checked = true;
        toggle.addEventListener("change", syncCategories);
    });
    syncCategories();

    // ---- Stylist: only show stylists who cover the chosen categories -----

    function syncStylists() {
        const chosen = new Set(selectedServices().map(function (s) { return s.dataset.category; }));
        const any = form.querySelector("#stylist-any");
        let selectedHidden = false;
        form.querySelectorAll('input[name="stylist"][data-categories]').forEach(function (input) {
            const covers = input.dataset.categories.split(" ").filter(Boolean);
            const show = !chosen.size || covers.some(function (id) { return chosen.has(id); });
            const label = input.nextElementSibling;
            input.hidden = !show;
            if (label) label.hidden = !show;
            if (!show && input.checked) selectedHidden = true;
        });
        if (selectedHidden && any) any.checked = true;
    }

    // ---- Time picker ------------------------------------------------------

    const picker = form.querySelector("[data-time-picker]");
    const readout = picker.querySelector("[data-time-readout]");
    const timeEnd = picker.querySelector("[data-time-end]");
    const timeStatus = picker.querySelector("[data-time-status]");
    const timeGroups = picker.querySelector("[data-time-groups]");

    // The chips are the no-JS control; the picker writes one hidden value instead.
    const startInput = document.createElement("input");
    startInput.type = "hidden";
    startInput.name = "start_time";
    form.appendChild(startInput);
    form.querySelectorAll('input[name="start_time"][type="radio"]').forEach(function (radio) {
        radio.disabled = true;
    });

    // Minutes since midnight of the picked start time; null until one is chosen.
    let pickedMinutes = /^\d{2}:\d{2}$/.test(picker.dataset.initial || "") ? toMinutes(picker.dataset.initial) : null;
    let renderedKey = "";

    function pickedTime() {
        return pickedMinutes;
    }

    function hhmm(minutes) {
        return String(Math.floor(minutes / 60)).padStart(2, "0") + ":" + String(minutes % 60).padStart(2, "0");
    }

    // Open times grouped Morning / Afternoon / Evening. Times that can't be
    // booked stay visible but disabled, so the day's shape is readable.
    const PARTS = [
        { label: "Morning", from: 0, to: 12 * 60 },
        { label: "Afternoon", from: 12 * 60, to: 17 * 60 },
        { label: "Evening", from: 17 * 60, to: 24 * 60 },
    ];

    function renderTimes() {
        const needed = totals().minutes;
        const key = [slotsState, dateInput.value, chosenStylistInput() ? chosenStylistInput().value : "", needed, pickedMinutes].join("|");
        if (key === renderedKey) return;
        renderedKey = key;
        const hadFocus = timeGroups.contains(document.activeElement);
        timeGroups.textContent = "";
        if (slotsState !== "ready" || !slotMap) return;
        const times = Object.keys(slotMap).sort();
        PARTS.forEach(function (part, p) {
            const inPart = times.filter(function (t) {
                const m = toMinutes(t);
                return m >= part.from && m < part.to;
            });
            if (!inPart.length) return;
            const group = document.createElement("div");
            group.className = "time-group";
            group.setAttribute("role", "radiogroup");
            const labelId = "time-part-" + p;
            const label = document.createElement("p");
            label.className = "time-group-label";
            label.id = labelId;
            label.textContent = part.label;
            group.setAttribute("aria-labelledby", labelId);
            const grid = document.createElement("div");
            grid.className = "option-grid option-grid--slots";
            inPart.forEach(function (t) {
                const slot = slotMap[t];
                const m = toMinutes(t);
                const short = needed && slot.free_minutes < needed;
                const usable = slot.available && !short;
                const input = document.createElement("input");
                input.type = "radio";
                input.className = "option-input";
                input.id = "time-" + t.replace(":", "");
                input.name = "time_pick";
                input.setAttribute("form", ""); // not submitted; start_time is
                input.value = t;
                input.disabled = !usable;
                input.checked = usable && m === pickedMinutes;
                const option = document.createElement("label");
                option.className = "option option--slot";
                option.htmlFor = input.id;
                option.textContent = format12(m);
                if (!usable) {
                    const why = document.createElement("span");
                    why.className = "visually-hidden";
                    why.textContent = slot.reason === "past" ? ", already passed"
                        : slot.reason === "booked" ? ", stylist booked" : ", too short for the selected services";
                    option.appendChild(why);
                }
                grid.appendChild(input);
                grid.appendChild(option);
            });
            group.appendChild(label);
            group.appendChild(grid);
            timeGroups.appendChild(group);
        });
        if (hadFocus && pickedMinutes !== null) {
            const again = document.getElementById("time-" + hhmm(pickedMinutes).replace(":", ""));
            if (again) again.focus({ preventScroll: true });
        }
    }

    // Quick date buttons: Today / Tomorrow / this Saturday, within the booking window.
    const earliestButton = picker.querySelector("[data-earliest]");
    function isoLocal(d) {
        return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
    }
    form.querySelectorAll("[data-quick-date]").forEach(function (button) {
        const base = new Date();
        base.setHours(0, 0, 0, 0);
        const offset = button.dataset.quickDate === "weekend" ? (6 - base.getDay() + 7) % 7 : Number(button.dataset.quickDate);
        const target = new Date(base.getFullYear(), base.getMonth(), base.getDate() + offset);
        const iso = isoLocal(target);
        if ((dateInput.min && iso < dateInput.min) || (dateInput.max && iso > dateInput.max)) button.hidden = true;
        button.addEventListener("click", function () {
            dateInput.value = iso;
            dateInput.dispatchEvent(new Event("change", { bubbles: true }));
            pickedMinutes = null;
            refreshTime();
        });
    });
    earliestButton.addEventListener("click", function () {
        const first = timeGroups.querySelector(".option-input:not(:disabled)");
        if (!first) return;
        first.checked = true;
        pickedMinutes = toMinutes(first.value);
        refreshTime();
        first.focus({ preventScroll: false });
    });

    timeGroups.addEventListener("change", function (event) {
        if (event.target.name !== "time_pick") return;
        pickedMinutes = toMinutes(event.target.value);
        refreshTime();
    });

    // Slot availability for the chosen date + stylist, fetched from the server.
    let slotMap = null; // { "HH:MM": slot } once loaded
    let slotsState = "idle"; // idle | loading | ready | error
    let slotsMessage = "";
    let slotsRequest = 0;

    function chosenStylistInput() {
        return form.querySelector('input[name="stylist"]:checked');
    }

    function loadSlots() {
        const date = dateInput.value;
        slotMap = null;
        if (!date || (dateInput.min && date < dateInput.min) || (dateInput.max && date > dateInput.max)) {
            slotsState = "idle";
            refreshTime();
            return;
        }
        const stylist = chosenStylistInput();
        const params = new URLSearchParams({ date: date, stylist: stylist ? stylist.value : "" });
        const ticket = ++slotsRequest;
        slotsState = "loading";
        refreshTime();
        fetch(slotsUrl + "?" + params.toString(), { headers: { Accept: "application/json" }, credentials: "same-origin" })
            .then(function (response) {
                return response.json().then(function (data) { return { ok: response.ok, data: data }; });
            })
            .then(function (result) {
                if (ticket !== slotsRequest) return;
                if (!result.ok) {
                    slotsState = "error";
                    slotsMessage = result.data.error || "Couldn't load times for that date.";
                } else {
                    slotMap = {};
                    result.data.slots.forEach(function (slot) { slotMap[slot.time] = slot; });
                    slotsState = "ready";
                }
                refreshTime();
            })
            .catch(function () {
                if (ticket !== slotsRequest) return;
                slotsState = "error";
                slotsMessage = "Couldn't load times. Check your connection and try again.";
                refreshTime();
            });
    }

    // Returns { ok, message, end } for the picked time.
    function timeVerdict() {
        const start = pickedTime();
        const minutes = totals().minutes;
        if (!dateInput.value) return { ok: false, message: "Pick a date to check this time." };
        if (slotsState === "loading") return { ok: false, message: "Checking times…" };
        if (slotsState === "error") return { ok: false, message: slotsMessage };
        if (slotsState !== "ready") return { ok: false, message: "Pick a date within the booking window." };
        if (start === null) return { ok: false, message: "Choose a start time." };
        const key = hhmm(start);
        const slot = slotMap[key];
        if (!slot) {
            return {
                ok: false,
                message: "We're open " + format12(toMinutes(openTime)) + " to " + format12(toMinutes(closeTime)) +
                    ". Pick a start time that finishes by closing.",
            };
        }
        if (slot.reason === "past") return { ok: false, message: "That time has already passed." };
        if (slot.reason === "booked") {
            const stylist = chosenStylistInput();
            const who = stylist && stylist.dataset.name ? stylist.dataset.name + " is" : "That slot is";
            return { ok: false, message: who + " booked then. Try another time." };
        }
        if (minutes && minutes > slot.free_minutes) {
            return {
                ok: false,
                message: "Your services take " + formatDuration(minutes) + ", but only " +
                    formatDuration(slot.free_minutes) + " are free from here.",
            };
        }
        return { ok: true, message: "Open.", end: minutes ? start + minutes : null };
    }

    function refreshTime() {
        const start = pickedMinutes;
        renderTimes();
        earliestButton.disabled = !timeGroups.querySelector(".option-input:not(:disabled)");
        readout.textContent = start === null ? "Pick a time" : format12(start);

        const verdict = timeVerdict();
        // Nothing picked yet is a prompt, not an error.
        const prompting = start === null && slotsState === "ready";
        timeStatus.textContent = verdict.ok ? "" : verdict.message;
        timeStatus.classList.toggle("is-problem", !verdict.ok && slotsState !== "loading" && !prompting);
        timeEnd.textContent = verdict.ok && verdict.end != null ? "· ends " + format12(verdict.end) : "";
        startInput.value = verdict.ok ? hhmm(start) : "";
        updateSummary();
    }
    dateInput.addEventListener("change", loadSlots);
    form.querySelectorAll('input[name="stylist"]').forEach(function (radio) {
        radio.addEventListener("change", loadSlots);
    });

    // ---- Summary bar ------------------------------------------------------

    function updateSummary() {
        if (!summary) return;
        const t = totals();
        if (!t.services.length) {
            summary.textContent = "Choose at least one service";
            return;
        }
        const parts = [
            t.services.length + " service" + (t.services.length === 1 ? "" : "s"),
            formatDuration(t.minutes),
        ];
        const verdict = timeVerdict();
        if (verdict.ok && verdict.end != null) parts.push("ends " + format12(verdict.end));
        summary.textContent = parts.join(" · ") + " · ";
        const strong = document.createElement("strong");
        strong.textContent = rupees.format(t.price);
        summary.appendChild(strong);
    }

    const clearButton = form.querySelector("[data-clear-services]");
    if (clearButton) {
        clearButton.addEventListener("click", function () {
            form.querySelectorAll('input[name="services"]:checked').forEach(function (box) { box.checked = false; });
            onServicesChanged();
        });
    }

    function onServicesChanged() {
        if (clearButton) {
            const n = form.querySelectorAll('input[name="services"]:checked').length;
            clearButton.hidden = n === 0;
            clearButton.textContent = "Clear all (" + n + ")";
        }
        syncCategories();
        syncStylists();
        refreshTime();
    }

    form.addEventListener("change", function (event) {
        if (event.target.name === "services") onServicesChanged();
        if (event.target.name === "booked_for_guest") updateProgress();
    });

    // ---- Step navigation --------------------------------------------------

    let current = 0;
    let navLockedUntil = 0;

    function currentStep() { return activeSteps()[current]; }

    const stepTitles = {
        who: "Who",
        services: "Services",
        stylist: "Stylist",
        datetime: "Date & time",
        guest: "Guest details",
        confirm: "Confirm",
    };
    const lead = document.querySelector("[data-lead]");

    function updateProgress() {
        const steps = activeSteps();
        const index = Math.min(current, steps.length - 1);
        const el = steps[index];
        if (!el) return;
        const text = progress.querySelector("[data-progress-text]");
        text.textContent = "";
        const strong = document.createElement("strong");
        strong.textContent = stepTitles[stepId(el)];
        text.appendChild(strong);
        text.appendChild(document.createTextNode(" · " + (index + 1) + " of " + steps.length));
        progress.querySelectorAll("[data-progress-step]").forEach(function (li) {
            const id = li.dataset.progressStep;
            const position = steps.findIndex(function (s) { return stepId(s) === id; });
            li.hidden = position === -1;
            li.classList.toggle("is-done", position !== -1 && position < index);
            li.classList.toggle("is-current", position === index);
            if (position === index) li.setAttribute("aria-current", "step");
            else li.removeAttribute("aria-current");
        });
        if (lead) lead.hidden = index !== 0;
        const last = index === steps.length - 1;
        backButton.hidden = index === 0;
        nextButton.hidden = last;
        submitButton.hidden = !last;
    }

    function buildReview() {
        const review = form.querySelector("[data-review]");
        review.textContent = "";
        const t = totals();
        const stylist = chosenStylistInput();
        const verdict = timeVerdict();
        const guestName = form.querySelector('input[name="guest_name"]').value.trim();
        const rows = [
            { label: "For", value: isGuest() ? guestName || "Guest" : "Myself", goto: isGuest() ? "guest" : "who" },
            {
                label: "Services",
                value: t.services.map(function (s) {
                    return s.dataset.name + " (" + rupees.format(Number(s.dataset.price)) + ")";
                }),
                goto: "services",
            },
            { label: "Stylist", value: stylist && stylist.value ? stylist.dataset.name : "Any available stylist", goto: "stylist" },
            { label: "When", value: whenText(verdict), goto: "datetime" },
            { label: "Total", value: rupees.format(t.price) + " · " + formatDuration(t.minutes), goto: "services" },
        ];
        const dl = document.createElement("dl");
        dl.className = "review-list";
        rows.forEach(function (row) {
            const dt = document.createElement("dt");
            dt.textContent = row.label;
            const dd = document.createElement("dd");
            const lines = document.createElement("span");
            lines.className = "review-lines";
            const values = Array.isArray(row.value) ? row.value : [row.value];
            values.forEach(function (text) {
                const line = document.createElement("span");
                line.className = "review-line";
                line.textContent = text;
                lines.appendChild(line);
            });
            dd.appendChild(lines);
            const edit = document.createElement("button");
            edit.type = "button";
            edit.className = "btn btn--quiet";
            edit.textContent = "Edit";
            edit.setAttribute("aria-label", "Edit " + row.label.toLowerCase());
            edit.addEventListener("click", function () { goToStepById(row.goto); });
            dd.appendChild(edit);
            dl.appendChild(dt);
            dl.appendChild(dd);
        });
        review.appendChild(dl);
    }

    function whenText(verdict) {
        if (!dateInput.value) return "—";
        const parts = dateInput.value.split("-").map(Number);
        const date = new Date(parts[0], parts[1] - 1, parts[2]);
        const day = date.toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
        const start = pickedTime();
        if (start === null) return day;
        const end = verdict.end != null ? " – " + format12(verdict.end) : "";
        return day + ", " + format12(start) + end;
    }

    function showStep(index, options) {
        const steps = activeSteps();
        current = Math.max(0, Math.min(index, steps.length - 1));
        navLockedUntil = Date.now() + 300;
        allSteps.forEach(function (el) {
            el.hidden = el !== steps[current];
            el.classList.remove("is-entering");
        });
        const el = steps[current];
        if (!reducedMotion.matches) {
            // Reflow so the animation restarts when returning to a step.
            void el.offsetWidth;
            el.classList.add("is-entering");
        }
        if (stepId(el) === "confirm") buildReview();
        updateProgress();
        if (!options || options.focus !== false) {
            const heading = el.querySelector("legend h2");
            if (heading) heading.focus({ preventScroll: true });
            const top = progress.getBoundingClientRect().top;
            if (top < 0) window.scrollTo({ top: window.scrollY + top - 16 });
        }
        if (!options || options.push !== false) {
            history.pushState({ step: stepId(el) }, "", "#" + el.id);
        }
    }

    function goToStepById(id, options) {
        const steps = activeSteps();
        const index = steps.findIndex(function (s) { return stepId(s) === id; });
        if (index !== -1) showStep(index, options);
    }

    // Per-step checks. Returns true when the step may be left.
    function validateStep(step) {
        clearJsErrors(step);
        const id = stepId(step);
        let firstBad = null;
        if (id === "services") {
            if (!selectedServices().length) {
                stepError(step, "Choose at least one service to continue.");
                return false;
            }
            return true;
        }
        if (id === "datetime") {
            if (!dateInput.value) {
                fieldError(dateInput, "Choose a date.");
                dateInput.focus();
                return false;
            }
            const verdict = timeVerdict();
            if (!verdict.ok) {
                timeStatus.classList.add("is-problem");
                const target = timeGroups.querySelector(".option-input:not(:disabled)") || dateInput;
                target.focus();
                return false;
            }
            return true;
        }
        if (id === "guest") {
            const name = form.querySelector('input[name="guest_name"]');
            const phone = form.querySelector('input[name="guest_phone"]');
            const email = form.querySelector('input[name="guest_email"]');
            if (!name.value.trim()) { fieldError(name, "Enter the guest's name."); firstBad = firstBad || name; }
            if (!/^\+?\d{10,13}$/.test(phone.value.trim())) {
                fieldError(phone, "Enter a phone number with 10-13 digits.");
                firstBad = firstBad || phone;
            }
            if (!email.value.trim() || !email.checkValidity()) {
                fieldError(email, "Enter a valid email address.");
                firstBad = firstBad || email;
            }
            if (firstBad) firstBad.focus();
            return !firstBad;
        }
        if (id === "confirm") {
            const name = form.querySelector('input[name="contact_name"]');
            const phone = form.querySelector('input[name="contact_phone"]');
            const email = form.querySelector('input[name="contact_email"]');
            if (!name.value.trim()) { fieldError(name, "Enter your name."); firstBad = firstBad || name; }
            if (!email.value.trim() || !email.checkValidity()) {
                fieldError(email, "Enter a valid email address.");
                firstBad = firstBad || email;
            }
            if (!/^\+?\d{10,13}$/.test(phone.value.trim())) {
                fieldError(phone, "Enter a phone number with 10-13 digits.");
                firstBad = firstBad || phone;
            }
            if (firstBad) firstBad.focus();
            return !firstBad;
        }
        return true;
    }

    nextButton.addEventListener("click", function () {
        if (Date.now() < navLockedUntil) return;
        if (validateStep(currentStep())) showStep(current + 1);
    });
    backButton.addEventListener("click", function () {
        if (Date.now() < navLockedUntil) return;
        if (current > 0) showStep(current - 1);
    });

    window.addEventListener("popstate", function (event) {
        const id = (event.state && event.state.step) || "who";
        const known = activeSteps().some(function (el) { return stepId(el) === id; });
        goToStepById(known ? id : "who", { push: false, focus: false });
    });

    // ---- Submit -----------------------------------------------------------

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
        // Enter inside a field on an earlier step moves forward instead of booking.
        const steps = activeSteps();
        if (current < steps.length - 1) {
            event.preventDefault();
            nextButton.click();
            return;
        }
        // Every earlier step must still hold; jump back to the first that doesn't.
        for (let i = 0; i < steps.length; i += 1) {
            if (!validateStep(steps[i])) {
                event.preventDefault();
                if (i !== current) showStep(i);
                return;
            }
        }
        submitting = true;
        if (submitButton) {
            submitButton.setAttribute("aria-disabled", "true");
            submitButton.textContent = "Booking…";
        }
    });

    // Coming back via the browser's back button restores the page from cache
    // with the button still saying "Booking…"; reset it.
    window.addEventListener("pageshow", function (event) {
        if (!event.persisted) return;
        submitting = false;
        form.querySelectorAll('.btn--primary[aria-disabled="true"]').forEach(function (button) {
            button.removeAttribute("aria-disabled");
            button.textContent = "Book appointment";
        });
    });

    // ---- Start ------------------------------------------------------------

    // Error summary links point at fields that may sit in a hidden step.
    const errors = document.getElementById("error-summary");
    if (errors) {
        errors.addEventListener("click", function (event) {
            const link = event.target.closest('a[href^="#"]');
            if (!link) return;
            const target = document.getElementById(link.getAttribute("href").slice(1));
            const step = target && target.closest(".wizard-step");
            if (!step) return;
            event.preventDefault();
            goToStepById(stepId(step), { focus: false });
            target.scrollIntoView({ block: "center" });
            if (typeof target.focus === "function") target.focus({ preventScroll: true });
        });
    }

    syncStylists();
    if (clearButton) {
        const n = form.querySelectorAll('input[name="services"]:checked').length;
        clearButton.hidden = n === 0;
        clearButton.textContent = "Clear all (" + n + ")";
    }
    loadSlots();
    refreshTime();

    // After a failed server check open the step holding the first error.
    const firstError = form.querySelector(".form-error");
    const errorStep = firstError && firstError.closest(".wizard-step");
    const startId = errorStep ? stepId(errorStep) : "who";
    if (errorStep && stepId(errorStep) === "guest" && !isGuest()) {
        form.querySelector("#for-guest").checked = true;
    }
    history.replaceState({ step: startId }, "", "#" + (errorStep ? errorStep.id : "section-who"));
    goToStepById(startId, { push: false, focus: Boolean(errorStep) });
    document.documentElement.classList.add("wizard-ready");
    if (errors) errors.focus();
}
