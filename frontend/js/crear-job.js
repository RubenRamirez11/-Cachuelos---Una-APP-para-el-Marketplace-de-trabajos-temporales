document.addEventListener("DOMContentLoaded", function () {

    const token = localStorage.getItem("access_token");

    if (!token) {
        window.location.href = "login.html";
        return;
    }

    const form = document.getElementById("job-form");

    form.addEventListener("submit", async function (e) {

        e.preventDefault();

        const titulo = document.getElementById("titulo").value.trim();
        const descripcion = document.getElementById("descripcion").value.trim();
        const pago = parseFloat(document.getElementById("pago").value);
        const ubicacion = document.getElementById("ubicacion").value.trim();
        const fecha = document.getElementById("fecha").value;

        if (!titulo || !ubicacion || !fecha || isNaN(pago)) {
            alert("Completa todos los campos obligatorios.");
            return;
        }

        try {

            const response = await fetch("http://127.0.0.1:8000/jobs", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + token
                },
                body: JSON.stringify({
                    titulo: titulo,
                    descripcion: descripcion || null,
                    pago: pago,
                    ubicacion: ubicacion,
                    fecha: fecha
                })
            });

            const data = await response.json();

            if (!response.ok) {
                alert(data.detail || data.error || "Error al crear el trabajo.");
                return;
            }

            alert("✅ Trabajo creado correctamente");

            // Redirigir a mis jobs
            window.location.href = "mis-jobs.html";

        } catch (error) {
            console.log(error);
            alert("Error de conexión con el servidor.");
        }

    });

});