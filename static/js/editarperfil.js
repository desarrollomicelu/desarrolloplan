function toggleEdit(field) {
    document.getElementById(`${field}-display`).style.display = 'none';
    document.getElementById(`${field}-input`).style.display = 'inline';
    document.querySelector(`#${field}-input + .edit-btn`).style.display = 'none';
    document.querySelector(`#${field}-input + .edit-btn + .save-btn`).style.display = 'inline';
}
 
function saveEdit(field) {
    const newValue = document.getElementById(`${field}-input`).value;
    fetch('/editar_perfil', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ field: field, value: newValue }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById(`${field}-display`).textContent = newValue;
            document.getElementById(`${field}-display`).style.display = 'inline';
            document.getElementById(`${field}-input`).style.display = 'none';
            document.querySelector(`#${field}-input + .edit-btn`).style.display = 'inline';
            document.querySelector(`#${field}-input + .edit-btn + .save-btn`).style.display = 'none';
        } else {
            alert('Error al actualizar el perfil');
        }
    });
}
 