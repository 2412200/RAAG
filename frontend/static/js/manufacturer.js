document.addEventListener("DOMContentLoaded", () => {

    console.log("manufacturer.js loaded");

    const specSelect = document.getElementById("specification");
    const form = document.getElementById("productform");
    const sections = document.querySelectorAll(".spec-section");

    console.log("specSelect:", specSelect);
    console.log("form:", form);
    console.log("sections:", sections);

    if (!specSelect) {
        console.error("specification dropdown not found");
        return;
    }

    if (!form) {
        console.error("productform not found");
        return;
    }

    function setSectionActive(section, active) {
        section.hidden = !active;

        const fields = section.querySelectorAll(
            "input, select, textarea"
        );

        fields.forEach(field => {
            field.disabled = !active;
        });
    }

    function showSection(specValue) {
        sections.forEach(section => {
            const isMatch = section.dataset.spec === specValue;
            setSectionActive(section, isMatch);
        });
    }

    // Hide all sections initially
    sections.forEach(section => {
        setSectionActive(section, false);
    });

    // Show selected section
    specSelect.addEventListener("change", function () {
        showSection(this.value);
    });

    // Form validation and async submission
    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        if (!specSelect.value) {
            alert("Please select a Product Specification.");
            return;
        }

        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                alert(data.message || "Product added successfully!");
                form.reset();
                // Hide all sections initially after reset
                sections.forEach(section => {
                    setSectionActive(section, false);
                });
                specSelect.value = "";
            } else {
                alert("Error: " + (data.detail || "Unable to add product."));
            }
        } catch (error) {
            console.error(error);
            alert("Network error. Please try again.");
        }
    });

});