// SSR Version - Minimal JS untuk UI interaktif saja
(function () {
  'use strict';

  // ── Header Mobile Toggle ────────────────────────────
  var headerToggle = document.getElementById('headerToggle');
  var headerNav = document.querySelector('.header__nav');
  if (headerToggle && headerNav) {
    headerToggle.addEventListener('click', function () {
      headerNav.classList.toggle('open');
    });

    // Close nav when clicking a link (mobile)
    var navLinks = headerNav.querySelectorAll('.header__nav-link');
    navLinks.forEach(function (link) {
      link.addEventListener('click', function () {
        headerNav.classList.remove('open');
      });
    });
  }

  // ── Sidebar Toggle (Admin) ──────────────────────────
  var sidebarToggle = document.getElementById('sidebarToggle');
  var sidebar = document.getElementById('sidebar');
  if (sidebarToggle && sidebar) {
    // Create overlay element dynamically
    var overlay = document.createElement('div');
    overlay.className = 'admin__sidebar-overlay';
    document.body.appendChild(overlay);

    function openSidebar() {
      sidebar.classList.add('open');
      overlay.classList.add('open');
      document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
      sidebar.classList.remove('open');
      overlay.classList.remove('open');
      document.body.style.overflow = '';
    }

    sidebarToggle.addEventListener('click', function () {
      if (sidebar.classList.contains('open')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });

    overlay.addEventListener('click', closeSidebar);

    // Close sidebar on window resize to desktop
    window.addEventListener('resize', function () {
      if (window.innerWidth > 900) {
        closeSidebar();
      }
    });
  }

  // ── Header User Dropdown ────────────────────────────
  var profile = document.querySelector('.header__profile');
  var dropdown = document.getElementById('headerDropdown');
  if (profile && dropdown) {
    profile.addEventListener('click', function (e) {
      e.stopPropagation();
      dropdown.classList.toggle('open');
    });
    document.addEventListener('click', function () {
      dropdown.classList.remove('open');
    });
  }

  // ── FAQ Accordion ───────────────────────────────────
  var faqQuestions = document.querySelectorAll('.faq__question');
  faqQuestions.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var answer = this.nextElementSibling;
      if (answer) {
        answer.classList.toggle('open');
        this.querySelector('.faq__arrow').classList.toggle('rotated');
      }
    });
  });

  // ── File Upload Preview ─────────────────────────────
  var uploadArea = document.getElementById('uploadArea');
  var uploadInput = document.getElementById('foto');
  var previews = document.getElementById('previews');
  if (uploadArea && uploadInput && previews) {
    uploadArea.addEventListener('click', function () { uploadInput.click(); });

    uploadInput.addEventListener('change', function () {
      previews.innerHTML = '';
      var max = Math.min(this.files.length, 3);
      for (var i = 0; i < max; i++) {
        var file = this.files[i];
        if (!file.type.match('image.*')) continue;
        var reader = new FileReader();
        reader.onload = (function (f) {
          return function (e) {
            var div = document.createElement('div');
            div.className = 'form__preview';
            div.innerHTML = '<img src="' + e.target.result + '" alt="Preview">'
              + '<button type="button" class="form__preview-remove" data-file="' + f.name + '">&times;</button>';
            div.querySelector('.form__preview-remove').addEventListener('click', function (e) {
              e.stopPropagation();
              div.remove();
              if (!previews.children.length) uploadInput.value = '';
            });
            previews.appendChild(div);
          };
        })(file);
        reader.readAsDataURL(file);
      }
    });
  }

  // ── Drag & Drop Upload ──────────────────────────────
  if (uploadArea) {
    uploadArea.addEventListener('dragover', function (e) {
      e.preventDefault();
      this.classList.add('dragover');
    });
    uploadArea.addEventListener('dragleave', function () {
      this.classList.remove('dragover');
    });
    uploadArea.addEventListener('drop', function (e) {
      e.preventDefault();
      this.classList.remove('dragover');
      if (uploadInput) uploadInput.files = e.dataTransfer.files;
    });
  }

})();
