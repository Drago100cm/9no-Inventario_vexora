document.addEventListener("DOMContentLoaded", () => {

    const forms = document.querySelectorAll(".validate-required");

    forms.forEach(form => {

        form.addEventListener("submit", function (e) {

            let valid = true;

            const requiredFields = form.querySelectorAll("[required]");

            requiredFields.forEach(field => {

                if (field.type === "checkbox") {

                    if (!field.checked) {
                        valid = false;
                        field.classList.add("is-invalid");
                    } else {
                        field.classList.remove("is-invalid");
                    }

                } else if (field.value.trim() === "") {

                    valid = false;
                    field.classList.add("is-invalid");

                } else {

                    field.classList.remove("is-invalid");
                }

            });

            if (!valid) {

                e.preventDefault();

                Swal.fire({
                    icon: "warning",
                    title: "Campos obligatorios",
                    text: "Los campos marcados con (*) son obligatorios.",
                    confirmButtonText: "Aceptar"
                });

            }

        });

    });

});