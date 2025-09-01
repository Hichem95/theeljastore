// JavaScript utilities for the Theelja Store site

document.addEventListener('DOMContentLoaded', function () {
    // Fade out the "added to cart" message after 3 seconds and bounce the cart icon
    var msg = document.querySelector('.added-message');
    if (msg) {
        // Find the cart link to animate
        var cartLink = document.querySelector('.cart-link');
        if (cartLink) {
            cartLink.classList.add('cart-bounce');
            // Remove the bounce class after the animation completes
            setTimeout(function () {
                cartLink.classList.remove('cart-bounce');
            }, 700);
        }
        // When an item is added, ensure the cart overlay shows next time
        localStorage.removeItem('cartOverlayClosed');
        setTimeout(function () {
            msg.style.opacity = '0';
            // Remove from the layout after fading out
            setTimeout(function () {
                msg.style.display = 'none';
            }, 600);
        }, 3000);
    }

    // Fade-in effect for the hero image container itself
    var hero = document.querySelector('.hero');
    if (hero) {
        hero.classList.add('fade-in');
    }

    // Cart overlay show/hide logic
    var overlay = document.querySelector('.cart-overlay');
    var cartLinkNav = document.querySelector('.cart-link');
    var closeBtn = document.querySelector('.cart-close');
    // On page load, if the user previously closed the overlay, keep it hidden
    if (overlay && localStorage.getItem('cartOverlayClosed') === 'true') {
        overlay.classList.remove('open');
    }
    // Toggle overlay when clicking cart icon in the header
    if (cartLinkNav && overlay) {
        cartLinkNav.addEventListener('click', function (e) {
            e.preventDefault();
            // Toggle open state
            if (overlay.classList.contains('open')) {
                overlay.classList.remove('open');
                localStorage.setItem('cartOverlayClosed', 'true');
            } else {
                overlay.classList.add('open');
                localStorage.removeItem('cartOverlayClosed');
            }
            applyCartShift();
        });
    }
    // Close overlay when clicking the close button
    if (closeBtn && overlay) {
        closeBtn.addEventListener('click', function () {
            overlay.classList.remove('open');
            localStorage.setItem('cartOverlayClosed', 'true');
            // Remove the shift and update margin
            document.body.classList.remove('cart-open');
            applyCartShift();
        });
    }

    // Shift content to make room for cart overlay when open
    function applyCartShift() {
        if (!overlay) return;
        // Determine overlay width
        var width = overlay.getBoundingClientRect().width;
        document.body.style.setProperty('--cart-width', width + 'px');
        if (overlay.classList.contains('open')) {
            document.body.classList.add('cart-open');
        } else {
            document.body.classList.remove('cart-open');
        }
    }
    // Apply initial shift if overlay is open
    applyCartShift();
    // Reapply shift on window resize
    window.addEventListener('resize', applyCartShift);

    // Theme toggle functionality
    var themeToggleBtn = document.getElementById('theme-toggle');
    // On load, set theme from localStorage
    var savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function () {
            document.body.classList.toggle('dark-theme');
            // Persist preference
            if (document.body.classList.contains('dark-theme')) {
                localStorage.setItem('theme', 'dark');
            } else {
                localStorage.setItem('theme', 'light');
            }
        });
    }

    // Scroll reveal for product items
    var productItems = document.querySelectorAll('.product-item');
    if ('IntersectionObserver' in window) {
        var observer = new IntersectionObserver(function (entries, obs) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('reveal');
                    obs.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        productItems.forEach(function (item) {
            observer.observe(item);
        });
    } else {
        // Fallback: reveal all items immediately
        productItems.forEach(function (item) {
            item.classList.add('reveal');
        });
    }

    // 3D tilt effect on product cards
    productItems.forEach(function (item) {
        item.addEventListener('mousemove', function (e) {
            var rect = item.getBoundingClientRect();
            var x = e.clientX - rect.left;
            var y = e.clientY - rect.top;
            var percentX = (x / rect.width) - 0.5;
            var percentY = (y / rect.height) - 0.5;
            var rotateY = percentX * 10; // max 10deg
            var rotateX = -percentY * 10;
            // Slight lift
            item.style.transform = 'translateY(-5px) rotateX(' + rotateX + 'deg) rotateY(' + rotateY + 'deg)';
        });
        item.addEventListener('mouseleave', function () {
            item.style.transform = '';
        });
    });

    // Parallax scrolling for hero background
    var heroBg = document.querySelector('.hero');
    if (heroBg) {
        window.addEventListener('scroll', function () {
            var offset = window.pageYOffset;
            // Adjust background position for a parallax effect
            heroBg.style.backgroundPosition = 'center ' + (offset * 0.4) + 'px';
        });
    }

    // Back to top button functionality
    var backToTopBtn = document.getElementById('back-to-top');
    if (backToTopBtn) {
        window.addEventListener('scroll', function () {
            // Show button after scrolling down a bit
            if (window.pageYOffset > 300) {
                backToTopBtn.style.display = 'flex';
            } else {
                backToTopBtn.style.display = 'none';
            }
        });
        backToTopBtn.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // Highlight the active navigation link based on the current path
    var navLinks = document.querySelectorAll('header nav a');
    var currentPath = window.location.pathname;
    navLinks.forEach(function (link) {
        var linkPath = link.getAttribute('href').split('?')[0];
        if (linkPath === currentPath) {
            link.classList.add('active');
        }
    });
});