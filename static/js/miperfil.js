document.addEventListener('DOMContentLoaded', function() {
  var dropdownToggle = document.querySelector('.custom-dropdown-toggle');
  var dropdownMenu = document.querySelector('.dropdown-menu');
  var miPerfil = document.querySelector('.dropdown-menu .custom-dropdown-item');
  var arrowIcon = dropdownToggle.querySelector('.custom-icon-arrow');

  function showDropdown() {
    dropdownMenu.style.display = 'block';
    miPerfil.style.display = 'block';
    arrowIcon.textContent = 'arrow_drop_up';
  }

  function hideDropdown() {
    dropdownMenu.style.display = 'none';
    miPerfil.style.display = 'none';
    arrowIcon.textContent = 'arrow_drop_down';
  }

  dropdownToggle.addEventListener('click', function(event) {
    event.preventDefault();
    if (dropdownMenu.style.display === 'block') {
      hideDropdown();
    } else {
      showDropdown();
    }
  });

  document.addEventListener('click', function(event) {
    var isClickInside = dropdownToggle.contains(event.target) || dropdownMenu.contains(event.target);
    if (!isClickInside && dropdownMenu.style.display === 'block') {
      hideDropdown();
    }
  });
  hideDropdown();
});