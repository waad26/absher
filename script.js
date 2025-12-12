document.addEventListener("DOMContentLoaded", () => {
  // Get all tab buttons
  const tabs = document.querySelectorAll(".tab-btn");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const target = tab.getAttribute("data-target");

      // Hide all tab contents
      document.querySelectorAll(".tab-content").forEach(content => {
        content.classList.remove("active");
      });

      // Show the targeted content
      document.getElementById(target).classList.add("active");

      // Set active class to the clicked tab
      tabs.forEach(t => {
        t.classList.remove("active");
      });

      tab.classList.add("active");
    });
  });
});

