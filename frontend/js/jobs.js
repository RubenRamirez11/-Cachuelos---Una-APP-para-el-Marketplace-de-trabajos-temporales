async function getJobs() {

    try {

        const response = await fetch("http://127.0.0.1:8000/jobs");

        if (!response.ok) {
            console.log("Error al obtener trabajos");
            return [];
        }

        const jobs = await response.json();
        return jobs;

    } catch (error) {
        console.log("Error de conexión:", error);
        return [];
    }
}