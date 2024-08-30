document.addEventListener('DOMContentLoaded', function() {
    var flashMessages = document.querySelectorAll('.flash1');
    flashMessages.forEach(function(flash) {
        // Cerrar manualmente
        var closeBtn = flash.querySelector('.close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                flash.remove();
            });
        }
       
        // Desaparecer automáticamente después de 5 segundos
        setTimeout(function() {
            flash.style.opacity = '0';
            flash.style.transition = 'opacity 0.5s ease';
            setTimeout(function() {
                flash.remove();
            }, 500);
        }, 3000);
    });
});