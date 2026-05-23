// Toggle mobile nav
const mobileNavButton = document.getElementById("mobile-nav-button");
const mobileNav = document.getElementById("mobile-nav");

if (mobileNavButton && mobileNav) {
  mobileNavButton.addEventListener("click", () => {
    mobileNav.classList.toggle("translate-x-0");
    mobileNav.classList.toggle("translate-x-60");
  });
}

// Close mobile nav when clicking outside
document.addEventListener("click", (event) => {
  const nav = document.getElementById("mobile-nav");
  const button = document.getElementById("mobile-nav-button");
  if (!nav || !button) return;

  // If nav is open and click is outside nav and button
  const navOpen = nav.classList.contains("translate-x-0");
  if (
    navOpen &&
    !nav.contains(event.target) &&
    !button.contains(event.target)
  ) {
    nav.classList.remove("translate-x-0");
    nav.classList.add("translate-x-60");
  }
});

document.querySelectorAll("[data-carousel]").forEach((carousel) => {
  const slides = Array.from(carousel.querySelectorAll(".hero-carousel__slide"));
  const dots = Array.from(carousel.querySelectorAll("[data-carousel-dot]"));
  const previousButton = carousel.querySelector("[data-carousel-prev]");
  const nextButton = carousel.querySelector("[data-carousel-next]");
  const intervalMs = 5000;
  let activeIndex = slides.findIndex((slide) =>
    slide.classList.contains("is-active"),
  );
  let autoplay;

  if (slides.length <= 1) return;
  if (activeIndex < 0) activeIndex = 0;

  const showSlide = (nextIndex) => {
    activeIndex = (nextIndex + slides.length) % slides.length;

    slides.forEach((slide, index) => {
      const isActive = index === activeIndex;
      slide.classList.toggle("is-active", isActive);
      slide.toggleAttribute("aria-hidden", !isActive);
    });

    dots.forEach((dot, index) => {
      const isActive = index === activeIndex;
      dot.classList.toggle("is-active", isActive);
      dot.toggleAttribute("aria-current", isActive);
    });
  };

  const startAutoplay = () => {
    window.clearInterval(autoplay);
    autoplay = window.setInterval(() => showSlide(activeIndex + 1), intervalMs);
  };

  const moveTo = (nextIndex) => {
    showSlide(nextIndex);
    startAutoplay();
  };

  previousButton?.addEventListener("click", () => moveTo(activeIndex - 1));
  nextButton?.addEventListener("click", () => moveTo(activeIndex + 1));
  dots.forEach((dot) => {
    dot.addEventListener("click", () => {
      moveTo(Number(dot.dataset.carouselDot));
    });
  });

  carousel.addEventListener("mouseenter", () => window.clearInterval(autoplay));
  carousel.addEventListener("focusin", () => window.clearInterval(autoplay));
  carousel.addEventListener("mouseleave", startAutoplay);
  carousel.addEventListener("focusout", startAutoplay);

  carousel.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") moveTo(activeIndex - 1);
    if (event.key === "ArrowRight") moveTo(activeIndex + 1);
  });

  showSlide(activeIndex);
  startAutoplay();
});
