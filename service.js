// Responsive images for service items
window.addEventListener('resize', function () {
    const serviceImages = document.querySelectorAll('.service-item img');

    serviceImages.forEach(function (image) {
        image.style.height = 'auto';
        image.style.width = '100%';
    });
});

// Hover effect for service item descriptions
document.addEventListener('DOMContentLoaded', function () {
    const serviceItems = document.querySelectorAll('.service-item');

    serviceItems.forEach(function (serviceItem) {
        serviceItem.addEventListener('mouseover', function () {
            this.style.backgroundColor = '#ddd';
        });

        serviceItem.addEventListener('mouseout', function () {
            this.style.backgroundColor = 'whitesmoke';
        });
    });
});
