$(document).ready(function() {
    var $submitButton = $('#botton');
    var timer;
 
    function activateButton() {
        $submitButton.prop('disabled', false);
        $submitButton.html('<span class="button-text">Recuperar</span>');
    }
 
    $('#loginForm').submit(function(e) {
        e.preventDefault();
       
        // Deshabilitar el botón inmediatamente después del clic
        $submitButton.prop('disabled', true);
        $submitButton.html('<span class="button-text">Enviando...</span>');
 
        // Iniciar el temporizador de 30 segundos
        clearTimeout(timer); // Limpiar cualquier temporizador existente
        timer = setTimeout(activateButton, 30000);
 
        $.ajax({
            url: '/recuperar_pass',
            type: 'POST',
            data: $(this).serialize(),
            success: function(response) {
                if (response.success) {
                    alert(response.message);
                    $('#codigoRecuperacionModal').modal('show');
                } else {
                    alert(response.message);
                }
            },
            error: function() {
                alert('Ocurrió un error. Por favor, intente nuevamente en 30 segundos.');
            }
        });
    });
    $('#verificarCodigo').click(function() {
        var codigo = $('#codigoRecuperacion').val();
        var email = $('#email').val();
        $.ajax({
            url: '/verificar_codigo',
            type: 'POST',
            data: {
                email: email,
                codigo: codigo
            },
            success: function(response) {
                if (response.success) {
                    alert(response.message);
                    $('#codigoRecuperacionModal').modal('hide');
                    $('#cambiarContrasenaModal').modal('show');
                } else {
                    alert(response.message);
                    // No cerramos el modal aquí
                }
            }
        });
    });
    // Nuevo código para manejar el cambio de contraseña
    $('#cambiarContrasena').click(function() {
        var nuevaContrasena = $('#nuevaContrasena').val();
        var email = $('#email').val();
        $.ajax({
            url: '/cambiar_contrasena',
            type: 'POST',
            data: {
                email: email,
                nueva_contrasena: nuevaContrasena
            },
            success: function(response) {
                if (response.success) {
                    alert(response.message);
                    $('#cambiarContrasenaModal').modal('hide');
                    window.location.href = '/';
                } else {
                    alert(response.message);
                }
            }
        });
    });
});