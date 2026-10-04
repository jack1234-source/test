document.addEventListener("DOMContentLoaded", () => {
  const root = document.documentElement;
  const themeToggle = document.querySelector("[data-theme-toggle]");
  const faqItems = document.querySelectorAll(".faq-item");
  const contactForm = document.querySelector("#contact-form");
  const formStatus = document.querySelector("#form-status");
  const infoCards = document.querySelectorAll(".info-card");
  const detailItems = document.querySelectorAll(".info-list li");

  const savedTheme = localStorage.getItem("nova-theme");
  if (savedTheme === "light") {
    root.setAttribute("data-theme", "light");
    if (themeToggle) {
      themeToggle.textContent = "🌙 Dark mode";
    }
  }

  themeToggle?.addEventListener("click", () => {
    const isLight = root.getAttribute("data-theme") === "light";
    const nextTheme = isLight ? "dark" : "light";
    root.setAttribute("data-theme", nextTheme);
    localStorage.setItem("nova-theme", nextTheme);
    themeToggle.textContent = nextTheme === "light" ? "🌙 Dark mode" : "☀️ Light mode";
  });

  infoCards.forEach((card) => {
    const activate = () => {
      infoCards.forEach((item) => {
        item.classList.remove("active");
        item.setAttribute("aria-expanded", "false");
      });
      card.classList.add("active");
      card.setAttribute("aria-expanded", "true");
    };

    card.addEventListener("click", activate);
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        activate();
      }
    });
  });

  detailItems.forEach((item) => {
    item.addEventListener("click", () => {
      detailItems.forEach((detailItem) => detailItem.classList.remove("active"));
      item.classList.add("active");
    });
  });

  faqItems.forEach((item) => {
    const trigger = item.querySelector("button");
    if (!trigger) return;

    trigger.addEventListener("click", () => {
      const isOpen = item.classList.contains("open");
      faqItems.forEach((faqItem) => {
        faqItem.classList.remove("open");
        faqItem.querySelector("button")?.setAttribute("aria-expanded", "false");
      });

      if (!isOpen) {
        item.classList.add("open");
        trigger.setAttribute("aria-expanded", "true");
      }
    });
  });

  contactForm?.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(contactForm);
    const payload = {
      name: String(formData.get("name") || "").trim(),
      email: String(formData.get("email") || "").trim(),
      projectType: String(formData.get("projectType") || "").trim(),
      message: String(formData.get("message") || "").trim(),
    };

    if (!payload.name || !payload.email || !payload.message) {
      formStatus.textContent = "Please complete your name, email, and project details.";
      formStatus.dataset.state = "error";
      return;
    }

    const submitButton = contactForm.querySelector("button[type='submit']");
    submitButton.disabled = true;
    submitButton.textContent = "Sending...";
    formStatus.textContent = "";
    formStatus.dataset.state = "idle";

    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Unable to send your message right now.");
      }

      formStatus.textContent = result.message;
      formStatus.dataset.state = "success";
      contactForm.reset();
    } catch (error) {
      formStatus.textContent = error.message || "Something went wrong. Please try again.";
      formStatus.dataset.state = "error";
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Send inquiry";
    }
  });
});
