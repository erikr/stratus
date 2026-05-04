(function () {
  function closest(el, selector) {
    while (el && el.nodeType === 1) {
      if (el.matches(selector)) return el;
      el = el.parentElement;
    }
    return null;
  }

  document.addEventListener("click", function (event) {
    var menuButton = closest(event.target, ".menu-button-2");
    if (menuButton) {
      var nav = document.querySelector(".w-nav-menu");
      if (nav) nav.classList.toggle("is-open");
      return;
    }

    var menuDropdownToggle = closest(event.target, ".toggle-dropdown");
    if (menuDropdownToggle) {
      var menuItem = closest(menuDropdownToggle, ".menu-item-has-children");
      if (menuItem) {
        var isOpen = menuItem.classList.toggle("is-open");
        menuDropdownToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
      }
      return;
    }

    var dropdownToggle = closest(event.target, ".w-dropdown-toggle");
    if (dropdownToggle) {
      var dropdown = closest(dropdownToggle, ".w-dropdown");
      if (dropdown) dropdown.classList.toggle("is-open");
      return;
    }

    var faqTop = closest(event.target, ".faq-top");
    if (faqTop) {
      var item = closest(faqTop, ".faq-item");
      if (item) item.classList.toggle("is-open");
    }
  });
})();
