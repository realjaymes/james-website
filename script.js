// James Praise — personal site
// Shared behavior: mobile nav toggle, scroll-reveal, directional card tilt.

document.addEventListener("DOMContentLoaded", function () {
  // ---- Mobile nav toggle ----
  var toggle = document.querySelector(".menu-toggle");
  var links = document.querySelector(".nav-links");
  if (toggle && links) {
    var closeMenu = function () {
      links.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
      toggle.textContent = "☰";
    };
    toggle.addEventListener("click", function () {
      var open = links.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.textContent = open ? "✕" : "☰";
    });
    links.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", closeMenu);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && links.classList.contains("is-open")) {
        closeMenu();
        toggle.focus();
      }
    });
    document.addEventListener("click", function (e) {
      if (links.classList.contains("is-open") && !links.contains(e.target) && e.target !== toggle) {
        closeMenu();
      }
    });
  }

  // ---- Scroll reveal (IntersectionObserver) ----
  var revealEls = document.querySelectorAll(".reveal-blur");
  if ("IntersectionObserver" in window && revealEls.length) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("is-visible"); });
  }

  // ---- Directional mouse tilt on cards ----
  var tiltEls = document.querySelectorAll(".case-card, .proj-card");
  var isTouch = window.matchMedia("(hover: none)").matches;
  if (!isTouch) {
    tiltEls.forEach(function (el) {
      el.addEventListener("mousemove", function (e) {
        var r = el.getBoundingClientRect();
        var x = (e.clientX - r.left) / r.width - 0.5;
        var y = (e.clientY - r.top) / r.height - 0.5;
        el.style.transform = "perspective(800px) rotateX(" + (y * -6) + "deg) rotateY(" + (x * 6) + "deg) translateY(-4px)";
      });
      el.addEventListener("mouseleave", function () {
        el.style.transform = "";
      });
    });
  }

  // ---- Work page category filter ----
  var tabs = document.querySelectorAll(".work-tab");
  if (tabs.length) {
    var categories = document.querySelectorAll("[data-work-category]");
    tabs.forEach(function (tab) {
      tab.setAttribute("aria-pressed", tab.classList.contains("is-active") ? "true" : "false");
      tab.addEventListener("click", function () {
        tabs.forEach(function (t) {
          t.classList.remove("is-active");
          t.setAttribute("aria-pressed", "false");
        });
        tab.classList.add("is-active");
        tab.setAttribute("aria-pressed", "true");
        var target = tab.getAttribute("data-target");
        categories.forEach(function (cat) {
          if (target === "all" || cat.getAttribute("data-work-category") === target) {
            cat.style.display = "";
          } else {
            cat.style.display = "none";
          }
        });
      });
    });
  }
});
