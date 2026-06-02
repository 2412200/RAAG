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

    // Form validation
    form.addEventListener("submit", function (e) {

        if (!specSelect.value) {
            e.preventDefault();
            alert("Please select a Product Specification.");
            return;
        }

        console.log("Form submitted");
    });

});
specSelect.addEventListener("change", function () {
    console.log("Selected:", this.value);
    showSection(this.value);
});