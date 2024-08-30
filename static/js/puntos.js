document.addEventListener('DOMContentLoaded', function() {
    const redeemButton = document.getElementById('redeem-button');
    const pointsInput = document.getElementById('points-input');
    const currentPointsDisplay = document.getElementById('current-points');
    const navPointsDisplay = document.getElementById('nav-points');

    function updatePointsDisplay(newTotal) {
        currentPointsDisplay.textContent = newTotal;
        navPointsDisplay.textContent = newTotal;

        [currentPointsDisplay, navPointsDisplay].forEach(element => {
            element.classList.add('updated');
            setTimeout(() => {
                element.classList.remove('updated');
            }, 1000);
        });
    }

    redeemButton.addEventListener('click', function() {
        const pointsToRedeem = pointsInput.value;

        fetch('/redimir_puntos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ points: pointsToRedeem })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updatePointsDisplay(data.new_total);
                pointsInput.value = '';
                alert('Puntos redimidos exitosamente');
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ocurrió un error al procesar la solicitud');
        });
    });
});