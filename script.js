// James Praise — personal site
// Shared behavior: mobile nav toggle, scroll-reveal, directional card tilt.

document.addEventListener("DOMContentLoaded", function () {
  // ---- Header solidifies on scroll (transparent over a dark portrait-hero, solid past it) ----
  var header = document.querySelector("header");
  if (header && document.body.classList.contains("has-dark-hero")) {
    var toggleHeaderScroll = function () {
      header.classList.toggle("is-scrolled", window.scrollY > 80);
    };
    toggleHeaderScroll();
    window.addEventListener("scroll", toggleHeaderScroll, { passive: true });
  }

  // ---- Mobile nav toggle (matches marketinginaction.xyz's .menu-button pattern) ----
  var toggle = document.querySelector(".menu-button");
  var links = document.querySelector(".nav-links");
  if (toggle && links) {
    var closeMenu = function () {
      links.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    };
    toggle.addEventListener("click", function () {
      var open = links.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
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

  // ---- Scroll-triggered reveal (blur + fade + rise), staggered per section — ported from marketinginaction.xyz ----
  (function () {
    var seen = new Map();
    document.querySelectorAll(".reveal-blur").forEach(function (el) {
      var parent = el.closest(".jobs-proof, .program-grid, .case-studies-grid, section") || el.parentElement;
      if (!seen.has(parent)) seen.set(parent, []);
      seen.get(parent).push(el);
    });

    function handleReveal(entries, observer) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        // Long scrolling lists (e.g. .talk-item rows) reveal one at a time as you scroll,
        // never all at once — staggering by DOM index would compound into multi-second
        // delays for later items. Only cluster-reveal small same-viewport groups.
        var delay = 0;
        if (!entry.target.closest(".talk-list")) {
          var siblings = seen.get(entry.target.closest(".jobs-proof, .program-grid, .case-studies-grid, section") || entry.target.parentElement) || [entry.target];
          var idx = siblings.indexOf(entry.target);
          delay = Math.max(idx, 0) * 90;
        }
        setTimeout(function () {
          entry.target.classList.add("is-visible");
        }, delay);
        observer.unobserve(entry.target);
      });
    }

    var observer = new IntersectionObserver(handleReveal, { threshold: 0.15, rootMargin: "0px 0px -80px 0px" });

    // A wrapper taller than the viewport can never reach a 15% intersection ratio while
    // scrolling through it (or crosses it only after most of it has already scrolled past),
    // leaving it stuck blurred/hidden the whole time it's on screen. Those get a near-zero
    // threshold instead so they reveal as soon as any part enters — normal-sized elements
    // keep the original 0.15 feel untouched.
    var tallObserver = new IntersectionObserver(handleReveal, { threshold: 0.01, rootMargin: "0px 0px -80px 0px" });

    document.querySelectorAll(".reveal-blur").forEach(function (el) {
      var isTall = el.offsetHeight > window.innerHeight * 0.9;
      (isTall ? tallObserver : observer).observe(el);
    });
  })();

  // ---- Click-to-expand image lightbox — opt-in via .zoomable-img ----
  (function () {
    var imgs = document.querySelectorAll(".zoomable-img");
    if (!imgs.length) return;

    var overlay = document.createElement("div");
    overlay.className = "img-lightbox";
    overlay.innerHTML =
      '<button type="button" class="img-lightbox-close" aria-label="Close">&times;</button>' +
      '<img class="img-lightbox-img" src="" alt="" />';
    document.body.appendChild(overlay);
    var overlayImg = overlay.querySelector(".img-lightbox-img");
    var closeBtn = overlay.querySelector(".img-lightbox-close");

    function openLightbox(src, alt) {
      overlayImg.src = src;
      overlayImg.alt = alt || "";
      overlay.classList.add("is-open");
      document.body.style.overflow = "hidden";
    }
    function closeLightbox() {
      overlay.classList.remove("is-open");
      document.body.style.overflow = "";
    }

    imgs.forEach(function (img) {
      img.setAttribute("role", "button");
      img.setAttribute("tabindex", "0");
      if (!img.hasAttribute("aria-label")) img.setAttribute("aria-label", "Click to view full size");
      img.addEventListener("click", function () {
        openLightbox(img.currentSrc || img.src, img.alt);
      });
      img.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          openLightbox(img.currentSrc || img.src, img.alt);
        }
      });
    });

    overlay.addEventListener("click", function (e) {
      if (e.target === overlay || e.target === overlayImg) closeLightbox();
    });
    closeBtn.addEventListener("click", closeLightbox);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && overlay.classList.contains("is-open")) closeLightbox();
    });
  })();

  // ---- Directional mouse tilt on cards ----
  var tiltEls = document.querySelectorAll(".case-study-card-v2, .program-card");
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

  // ---- Case studies filter (Work page: Type — Client Work / Side Projects / Pitch Microsites —
  //      and Service — Positioning, GTM, Lifecycle, etc. Clicking a button in one dimension
  //      resets the other to "all", so only one dimension is ever actively filtering at once,
  //      same behavior as the MIA consulting case-studies page this is ported from.) ----
  document.querySelectorAll(".case-studies-sidebar-filters").forEach(function (sidebar) {
    var grid = document.querySelector(".case-studies-grid");
    if (!grid) return;
    var cards = grid.querySelectorAll(".case-study-card-v2");
    var empty = document.querySelector(".case-studies-empty");
    var active = { type: "all", service: "all" };

    // "Blueprints" (pitch microsites) are private, one-company pitches: never part of
    // the public "All" view or its count, only reachable by explicitly filtering to
    // type=microsite (via the hidden button or a direct #type=microsite link).
    var publicCount = 0;
    cards.forEach(function (card) {
      var types = (card.getAttribute("data-tags") || "").split(" ");
      if (types.indexOf("microsite") === -1) publicCount++;
    });
    document.querySelectorAll(".csf-count").forEach(function (el) {
      el.textContent = "(" + publicCount + ")";
    });

    function applyFilters() {
      var visibleCount = 0;
      cards.forEach(function (card) {
        var types = (card.getAttribute("data-tags") || "").split(" ");
        var isMicrosite = types.indexOf("microsite") !== -1;
        var matchesType =
          active.type === "microsite" ? isMicrosite : active.type === "all" ? !isMicrosite : types.indexOf(active.type) !== -1;
        var services = (card.getAttribute("data-service") || "").split(" ");
        var matchesService = active.service === "all" || services.indexOf(active.service) !== -1;
        var show = matchesType && matchesService;
        card.hidden = !show;
        if (show) visibleCount++;
      });
      if (empty) empty.hidden = visibleCount !== 0;
    }

    function setActive(dim, value) {
      var group = sidebar.querySelectorAll('.case-filter-btn[data-filter-dim="' + dim + '"]');
      group.forEach(function (b) {
        b.classList.toggle("is-active", b.getAttribute("data-filter") === value);
      });
      active[dim] = value;
    }

    var buttons = sidebar.querySelectorAll(".case-filter-btn");
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var dim = btn.getAttribute("data-filter-dim");
        var otherDim = dim === "type" ? "service" : "type";
        setActive(dim, btn.getAttribute("data-filter"));
        setActive(otherDim, "all");
        applyFilters();
      });
    });

    // Auto-filter from URL hash, e.g. /work/#filter=positioning (service) or /work/#type=side
    var serviceMatch = window.location.hash.match(/filter=([a-z-]+)/);
    var typeMatch = window.location.hash.match(/type=([a-z-]+)/);
    if (serviceMatch || typeMatch) {
      if (serviceMatch) {
        var serviceBtn = sidebar.querySelector('.case-filter-btn[data-filter-dim="service"][data-filter="' + serviceMatch[1] + '"]');
        if (serviceBtn) serviceBtn.click();
      } else if (typeMatch) {
        var typeBtn = sidebar.querySelector('.case-filter-btn[data-filter-dim="type"][data-filter="' + typeMatch[1] + '"]');
        if (typeBtn) typeBtn.click();
      }
      // Filtering alone leaves the page scrolled to the top, so a hash link
      // like /work/#type=side reads as "did nothing" until the visitor
      // scrolls down manually. Jump to the grid itself, same as #case-studies.
      var caseStudiesSection = document.getElementById("case-studies");
      if (caseStudiesSection) caseStudiesSection.scrollIntoView();
    }
  });

  // ---- Typewriter cycling word (e.g. homepage hero: "I build/write/speak/teach") ----
  document.querySelectorAll("[data-typewriter]").forEach(function (el) {
    var words;
    try {
      words = JSON.parse(el.getAttribute("data-typewriter"));
    } catch (e) {
      return;
    }
    if (!words || !words.length) return;

    var wordIndex = 0;
    var charIndex = 0;
    var deleting = false;
    var typeSpeed = 90;
    var deleteSpeed = 45;
    var pauseAfterType = 1400;
    var pauseAfterDelete = 300;

    function tick() {
      var currentWord = words[wordIndex];
      if (!deleting) {
        charIndex++;
        el.textContent = currentWord.slice(0, charIndex);
        if (charIndex === currentWord.length) {
          deleting = true;
          setTimeout(tick, pauseAfterType);
          return;
        }
        setTimeout(tick, typeSpeed);
      } else {
        charIndex--;
        el.textContent = currentWord.slice(0, charIndex);
        if (charIndex === 0) {
          deleting = false;
          wordIndex = (wordIndex + 1) % words.length;
          setTimeout(tick, pauseAfterDelete);
          return;
        }
        setTimeout(tick, deleteSpeed);
      }
    }
    tick();
  });

  // ---- Generic tab/panel toggle (e.g. Speaking page: Speaking Engagements / Media Features) ----
  document.querySelectorAll("[data-tabs]").forEach(function (group) {
    var tabs = group.querySelectorAll("[data-tab-target]");
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        var target = tab.getAttribute("data-tab-target");
        tabs.forEach(function (t) {
          t.classList.toggle("is-active", t === tab);
        });
        document.querySelectorAll("[data-tab-panel]").forEach(function (panel) {
          panel.hidden = panel.getAttribute("data-tab-panel") !== target;
        });
      });
    });
  });

  // ---- Year filter for talk-grid cards (e.g. Writing page, Speaking page) ----
  document.querySelectorAll("[data-year-filter]").forEach(function (group) {
    var key = group.getAttribute("data-year-filter");
    var panel = null;
    document.querySelectorAll('[data-tab-panel="' + key + '"]').forEach(function (p) {
      if (p.querySelector(".talk-grid")) panel = p;
    });
    if (!panel) return;
    var cards = panel.querySelectorAll("[data-year-card]");
    var pills = group.querySelectorAll("[data-year]");
    pills.forEach(function (pill) {
      pill.addEventListener("click", function () {
        pills.forEach(function (p) {
          p.classList.toggle("is-active", p === pill);
        });
        var year = pill.getAttribute("data-year");
        cards.forEach(function (card) {
          card.style.display = year === "all" || card.getAttribute("data-year-card") === year ? "" : "none";
        });
      });
    });
  });

  // ---- Case study card click tracking (GA4 via GTM custom event) ----
  document.querySelectorAll(".case-study-card-v2, .case-study-pitch-card").forEach(function (card) {
    card.addEventListener("click", function () {
      var href = card.getAttribute("href") || "";
      var slug = href.replace(/^\/work\//, "").replace(/\/$/, "");
      window.dataLayer = window.dataLayer || [];
      window.dataLayer.push({
        event: "case_study_click",
        case_study_slug: slug,
        case_study_type: card.classList.contains("case-study-pitch-card") ? "pitch" : (card.getAttribute("data-tags") || "")
      });
    });
  });

  // ---- Pitch deck: interactive slide navigation for personalized job-pitch pages ----
  var pitchDeck = document.querySelector(".pitch-deck");
  if (pitchDeck) {
    var slides = Array.prototype.slice.call(pitchDeck.querySelectorAll(".pitch-slide"));
    var current = 0;

    var prevBtn = document.createElement("button");
    prevBtn.className = "pitch-nav-arrow pitch-nav-prev";
    prevBtn.setAttribute("aria-label", "Previous slide");
    prevBtn.innerHTML = "&#8592;";

    var nextBtn = document.createElement("button");
    nextBtn.className = "pitch-nav-arrow pitch-nav-next";
    nextBtn.setAttribute("aria-label", "Next slide");
    nextBtn.innerHTML = "&#8594;";

    var progress = document.createElement("div");
    progress.className = "pitch-progress";
    var dots = slides.map(function (_, i) {
      var dot = document.createElement("button");
      dot.className = "pitch-progress-dot";
      dot.setAttribute("aria-label", "Go to slide " + (i + 1));
      dot.addEventListener("click", function () { goTo(i); });
      progress.appendChild(dot);
      return dot;
    });

    document.body.appendChild(prevBtn);
    document.body.appendChild(nextBtn);
    document.body.appendChild(progress);

    function goTo(i) {
      current = Math.max(0, Math.min(slides.length - 1, i));
      slides.forEach(function (s, idx) { s.classList.toggle("is-active", idx === current); });
      dots.forEach(function (d, idx) { d.classList.toggle("is-active", idx === current); });
      prevBtn.disabled = current === 0;
      nextBtn.disabled = current === slides.length - 1;
    }

    prevBtn.addEventListener("click", function () { goTo(current - 1); });
    nextBtn.addEventListener("click", function () { goTo(current + 1); });

    document.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") goTo(current + 1);
      if (e.key === "ArrowLeft") goTo(current - 1);
    });

    goTo(0);
  }
});
