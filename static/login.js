// ============================================================
//  login.js — Maneja el formulario de login
//  Envía las credenciales al backend Python y redirige
// ============================================================

document.querySelector('form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const usuario  = document.getElementById('name').value.trim();
    const password = document.getElementById('password').value.trim();
    const btnLogin = document.querySelector('.btn-login');

    // Feedback visual mientras espera
    btnLogin.textContent = 'Verificando...';
    btnLogin.disabled = true;

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ usuario, password })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // Login exitoso → redirige a la tabla de alumnos
            window.location.href = '/tabla';
        } else {
            mostrarError(data.mensaje || 'Credenciales incorrectas');
        }

    } catch (error) {
        mostrarError('No se pudo conectar con el servidor');
    } finally {
        btnLogin.textContent = 'Ingresar';
        btnLogin.disabled = false;
    }
});

function mostrarError(mensaje) {
    // Elimina error previo si existe
    const previo = document.querySelector('.error-msg');
    if (previo) previo.remove();

    const div = document.createElement('div');
    div.className = 'error-msg';
    div.textContent = mensaje;
    div.style.cssText = `
        background: #fff0f0;
        color: #c0392b;
        border: 1px solid #e74c3c;
        border-radius: 6px;
        padding: 10px 14px;
        margin-top: 12px;
        font-size: 0.875rem;
        text-align: center;
    `;

    document.querySelector('.btn-login').insertAdjacentElement('afterend', div);
}