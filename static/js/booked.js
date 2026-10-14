// Booked page: share the appointment details (Web Share, else copy to clipboard).
(function () {
    "use strict";
    var button = document.querySelector("[data-share]");
    var status = document.querySelector("[data-share-status]");
    if (!button) return;

    function say(text) {
        if (status) status.textContent = text;
    }

    function copy(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text);
        }
        return Promise.reject(new Error("no clipboard"));
    }

    button.addEventListener("click", function () {
        var text = button.dataset.shareText;
        if (navigator.share) {
            navigator.share({ title: button.dataset.shareTitle, text: text }).catch(function () {});
            return;
        }
        copy(text).then(
            function () { say("Details copied. Paste them into a message."); },
            function () { say(text); }
        );
    });
})();
