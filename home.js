document.addEventListener("DOMContentLoaded", function () {
    const serviceItems = document.querySelectorAll(".service-item");

    serviceItems.forEach((item) => {
        item.addEventListener("mouseover", function () {
            // Add hover styles if needed
            item.style.backgroundColor = "#ddd";
        });

        item.addEventListener("mouseout", function () {
            // Remove hover styles if needed
            item.style.backgroundColor = "whitesmoke";
        });

        item.addEventListener("click", function () {
            const serviceName = item.getAttribute("data-service");
            // Open registration page or perform any desired action
            alert(`Opening registration page for ${serviceName}`);
        });
    });
});
let slideIndex = 1;
showSlides(slideIndex);

function plusSlides(n) {
    showSlides(slideIndex += n);
}

function currentSlide(n) {
    showSlides(slideIndex = n);
}

function showSlides(n) {
    let i;
    let slides = document.getElementsByClassName("mySlides");
    let dots = document.getElementsByClassName("dot");
    if (n > slides.length) { slideIndex = 1 }
    if (n < 1) { slideIndex = slides.length }
    for (i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";
    }
    for (i = 0; i < dots.length; i++) {
        dots[i].className = dots[i].className.replace(" active", "");
    }
    slides[slideIndex - 1].style.display = "block";
    dots[slideIndex - 1].className += " active";
}

// Automatically transition to the next slide every 3 seconds
setInterval(function () {
    plusSlides(1);
}, 4000);