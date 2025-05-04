// Toggle mobile nav
document.getElementById("mobile-nav-button").addEventListener("click", () => {
  document.getElementById("mobile-nav").classList.toggle("translate-x-0");
  document.getElementById("mobile-nav").classList.toggle("translate-x-60");
});

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
