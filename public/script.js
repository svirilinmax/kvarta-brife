// ==========================================================================
// Кварта — script.js
// ==========================================================================

(function () {
  "use strict";

  // ---------- UTM + referrer ----------

  function collectAttribution() {
    const params = new URLSearchParams(window.location.search);
    const utm = {};
    ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"].forEach((k) => {
      const v = params.get(k);
      if (v) utm[k] = v;
    });
    utm.referrer = document.referrer || "";
    utm.landing_page = window.location.href;
    try {
      sessionStorage.setItem("kvarta_utm", JSON.stringify(utm));
    } catch (_) {
      // sessionStorage может быть недоступен (приватный режим)
    }
  }

  function getAttribution() {
    try {
      const raw = sessionStorage.getItem("kvarta_utm");
      return raw ? JSON.parse(raw) : {};
    } catch (_) {
      return {};
    }
  }

  // ---------- Телефон ----------

  // Визуальная маска: (XX) XXX-XX-XX
  function formatPhoneInput(value) {
    let digits = value.replace(/\D/g, "");

    // Если человек случайно вставил +375 или 80 — убираем их,
    // так как +375 уже зафиксирован на экране
    if (digits.startsWith("375")) digits = digits.slice(3);
    if (digits.startsWith("80")) digits = digits.slice(2);

    // Ограничиваем 9 цифрами (код оператора + номер)
    digits = digits.slice(0, 9);

    let formatted = "";
    if (digits.length > 0) formatted += "(" + digits.slice(0, 2);
    if (digits.length >= 3) formatted += ") " + digits.slice(2, 5);
    if (digits.length >= 6) formatted += "-" + digits.slice(5, 7);
    if (digits.length >= 8) formatted += "-" + digits.slice(7, 9);

    return formatted;
  }

  // Для отправки на бэк: возвращает "375291234567"
  function getFullPhone(inputValue) {
    const digits = inputValue.replace(/\D/g, "");
    if (!digits) return "";
    return "375" + digits;
  }

  // Проверка на валидность (9 цифр после +375)
  function isValidPhone(inputValue) {
    const digits = inputValue.replace(/\D/g, "");
    return digits.length === 9;
  }

  // ---------- CTA-кнопки ----------

  function bindCtaButtons() {
    const interestSelect = document.getElementById("interest");
    const commentField = document.getElementById("comment");
    const form = document.getElementById("form");

    document.querySelectorAll("[data-interest]").forEach((btn) => {
      btn.addEventListener("click", function (e) {
        // 1. Ставим interest (order / subscription / question)
        if (interestSelect && this.dataset.interest) {
          interestSelect.value = this.dataset.interest;
        }

        // 2. Пишем выбранный продукт в комментарий (если есть)
        if (commentField && this.dataset.product) {
          const product = this.dataset.product;
          const current = commentField.value.trim();

          if (!current) {
            commentField.value = product;
          } else if (!current.includes(product)) {
            commentField.value = `${product}. ${current}`;
          }
        }

        // 3. Скролл к форме
        if (form) {
          form.scrollIntoView({ behavior: "smooth", block: "start" });
          const firstInput = document.getElementById("name");
          if (firstInput) {
            setTimeout(() => firstInput.focus({ preventScroll: true }), 400);
          }
        }
      });
    });
  }

    // ---------- Кнопка Наверх ----------

  function bindScrollTop() {
    const btn = document.getElementById("scroll-top");
    if (!btn) return;

    window.addEventListener("scroll", () => {
      if (window.scrollY > 400) {
        btn.classList.add("is-visible");
      } else {
        btn.classList.remove("is-visible");
      }
    }, { passive: true });

    btn.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // ---------- Валидация ----------

  function setFieldError(fieldWrap, message) {
    if (!fieldWrap) return;
    fieldWrap.classList.add("field-error");
    const hint = fieldWrap.querySelector(".field-hint");
    if (hint) hint.textContent = message;
  }

  function clearFieldError(fieldWrap) {
    if (!fieldWrap) return;
    fieldWrap.classList.remove("field-error");
    const hint = fieldWrap.querySelector(".field-hint");
    if (hint) hint.textContent = "Введите код оператора и номер";
  }

  // ---------- Состояния формы ----------

  function showMessage(text, type) {
    const el = document.getElementById("form-message");
    if (!el) return;
    el.textContent = text;
    el.className = "form-message is-visible " + (type || "");
  }

  function hideMessage() {
    const el = document.getElementById("form-message");
    if (!el) return;
    el.className = "form-message";
    el.textContent = "";
  }

  function setSubmitting(btn, submitting) {
    if (!btn) return;
    if (submitting) {
      btn.dataset.original = btn.textContent;
      btn.textContent = "Отправляем…";
      btn.disabled = true;
    } else {
      btn.textContent = btn.dataset.original || "Отправить заявку";
      btn.disabled = false;
    }
  }

  // ---------- Отправка ----------

  async function submitForm(e) {
    e.preventDefault();

    const form = e.currentTarget;
    const btn = document.getElementById("submit-btn");
    const phoneInput = document.getElementById("phone");
    const phoneWrap = phoneInput.closest(".field");

    hideMessage();

    // Honeypot
    const honey = form.querySelector('input[name="website"]');
    if (honey && honey.value) {
      // Тихо «принимаем» — бот думает, что всё ок
      showMessage("Заявка принята. Мы свяжемся с вами.", "is-success");
      form.reset();
      return;
    }

    // Валидация телефона
    if (!isValidPhone(phoneInput.value)) {
      setFieldError(phoneWrap, "Введите белорусский номер: +375 (29) 123-45-67");
      phoneInput.focus();
      return;
    }
    clearFieldError(phoneWrap);

    // Сбор данных
    const fd = new FormData(form);
    const payload = {
      name: (fd.get("name") || "").toString().trim(),
      phone: getFullPhone(phoneInput.value), // Отправляем 375XXXXXXXXX
      interest: (fd.get("interest") || "").toString(),
      comment: (fd.get("comment") || "").toString().trim() || null,
    };

    const attribution = getAttribution();
    Object.keys(attribution).forEach((k) => {
      if (attribution[k]) payload[k] = attribution[k];
    });

    setSubmitting(btn, true);

    try {
      const resp = await fetch("/api/lead", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await resp.json().catch(() => ({}));

      if (resp.ok && data.status === "ok") {
        showMessage("Заявка принята. Перезвоним в течение рабочего дня.", "is-success");
        form.reset();
      } else if (resp.ok && data.status === "duplicate") {
        showMessage(
          "Заявка уже принята. Мы свяжемся с вами — повторно отправлять не нужно.",
          "is-duplicate"
        );
        form.reset();
      } else if (resp.status === 422) {
        const errors = data.errors || {};
        if (errors.phone) setFieldError(phoneWrap, errors.phone);
        showMessage(
          data.message || "Проверьте обязательные поля и попробуйте снова.",
          "is-error"
        );
      } else if (resp.status === 429) {
        showMessage(
          data.message || "Слишком много заявок. Попробуйте позже.",
          "is-error"
        );
      } else {
        showMessage(
          "Не удалось отправить. Позвоните нам: +375 (29) 123-45-67.",
          "is-error"
        );
      }
    } catch (_) {
      showMessage(
        "Сеть недоступна. Проверьте интернет или позвоните: +375 (29) 123-45-67.",
        "is-error"
      );
    } finally {
      setSubmitting(btn, false);
    }
  }

    // ---------- Init ----------

  function init() {
    collectAttribution();
    bindCtaButtons();
    bindScrollTop(); // ← добавили

    const form = document.getElementById("lead-form");
    if (form) {
      form.addEventListener("submit", submitForm);

      // Кнопка "Очистить"
      const resetBtn = document.getElementById("reset-btn");
      if (resetBtn) {
        resetBtn.addEventListener("click", () => {
          form.reset();
          hideMessage();
          clearFieldError(document.getElementById("phone").closest(".field"));
        });
      }
    }

    // Маска телефона при вводе
    const phone = document.getElementById("phone");
    if (phone) {
      phone.addEventListener("input", function () {
        const start = this.selectionStart;
        const oldLen = this.value.length;

        this.value = formatPhoneInput(this.value);

        const newLen = this.value.length;
        if (start < oldLen) {
          this.setSelectionRange(Math.max(0, start - (oldLen - newLen)), Math.max(0, start - (oldLen - newLen)));
        } else {
          this.setSelectionRange(newLen, newLen);
        }

        const wrap = this.closest(".field");
        if (wrap && wrap.classList.contains("field-error")) {
          clearFieldError(wrap);
        }
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
