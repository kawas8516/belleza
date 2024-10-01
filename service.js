// Smooth scroll effect for navigation links
document.addEventListener("DOMContentLoaded", function() {
    const navLinks = document.querySelectorAll('nav a');

    navLinks.forEach(function(navLink) {
        navLink.addEventListener('click', function(event) {
            event.preventDefault();

            const targetSectionId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetSectionId);

            if (targetSection) {
                window.scrollTo({
                    top: targetSection.offsetTop - document.querySelector('header').offsetHeight,
                    behavior: 'smooth'
                });
            }
        });
    });
});

// Responsive images for service items
window.addEventListener('resize', function() {
    const serviceImages = document.querySelectorAll('#service-item img');
    
    serviceImages.forEach(function(image) {
        image.style.height = 'auto';
        image.style.width = '100%';
    });
});

// Hover effect for service item descriptions
const serviceItems = document.querySelectorAll('#service-item');

serviceItems.forEach(function(serviceItem) {
    serviceItem.addEventListener('mouseover', function() {
        this.style.backgroundColor = '#ddd'; // Change background color on hover
    });

    serviceItem.addEventListener('mouseout', function() {
        this.style.backgroundColor = 'whitesmoke'; // Revert to original color
    });
});

// Social media share buttons (Assuming you have share links in the footer)
const socialMediaLinks = document.querySelectorAll('#foot a');

socialMediaLinks.forEach(function(link) {
    link.addEventListener('click', function(event) {
        event.preventDefault();
        // You can add logic here to handle sharing on social media platforms
        alert('Social media sharing is not implemented in this example.');
    });
});
