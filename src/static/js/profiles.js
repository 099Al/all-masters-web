// static/js/profiles.js
(() => {
  "use strict";

  // ------------- Helpers -------------
  async function fetchJson(url, options) {
    const resp = await fetch(url, options);
    if (!resp.ok) {
      const text = await resp.text().catch(() => "");
      throw new Error(`${resp.status} ${resp.statusText}${text ? " — " + text : ""}`);
    }
    return resp.json();
  }

  function getLineHeight(el) {
    const cs = window.getComputedStyle(el);
    const lh = parseFloat(cs.lineHeight);
    if (!Number.isNaN(lh)) return lh;
    const fs = parseFloat(cs.fontSize) || 14;
    return fs * 1.2;
  }

  function adjustAboutWrappers() {
    document.querySelectorAll(".about-wrapper").forEach(wrapper => {
      const content = wrapper.querySelector(".about-content");
      const text = wrapper.querySelector(".about-text");
      const toggleBtn = wrapper.closest(".card").querySelector(".about-toggle");

      const lineHeight = getLineHeight(text);
      const maxLines = 5;
      const maxHeight = lineHeight * maxLines;
      const textHeight = text.scrollHeight;
      const contentHeight = content.scrollHeight;

      if (textHeight / lineHeight >= maxLines || contentHeight > maxHeight) {
        content.style.maxHeight = `${maxHeight}px`;
        content.classList.add("clamped");
        toggleBtn.style.display = "";
      } else {
        content.style.maxHeight = "";
        content.classList.remove("clamped");
        toggleBtn.style.display = "none";
      }
    });
  }

  function afterDom(fn) {
    requestAnimationFrame(() => setTimeout(fn, 0));
  }

  function getCaretState(el) {
    if (!el || !("selectionStart" in el)) return null;
    return { el, start: el.selectionStart, end: el.selectionEnd };
  }

  function restoreCaret(state) {
    if (!state) return false;
    const { el, start, end } = state;
    if (!document.contains(el)) return false;
    el.focus();
    try { el.setSelectionRange(start ?? el.value.length, end ?? el.value.length); } catch {}
    return true;
  }

  function focusComposerIn(modalEl) {
    const ta = modalEl?.querySelector(".modal-footer textarea");
    if (ta) {
      ta.focus();
      try {
        const len = ta.value.length;
        ta.setSelectionRange(len, len);
      } catch {}
    }
  }

  // ------------- About: show/hide -------------
  function initAbout() {
    adjustAboutWrappers();
    window.addEventListener("resize", adjustAboutWrappers);
    document.addEventListener("click", (e) => {
      const btn = e.target.closest(".about-toggle");
      if (!btn) return;
      const card = btn.closest(".card");
      const content = card.querySelector(".about-content");
      if (content.classList.contains("clamped")) {
        content.style.maxHeight = "";
        content.classList.remove("clamped");
        btn.textContent = "Свернуть";
      } else {
        const text = content.querySelector(".about-text");
        const maxHeight = getLineHeight(text) * 5;
        content.style.maxHeight = `${maxHeight}px`;
        content.classList.add("clamped");
        btn.textContent = "Показать больше";
      }
    });
    window.addEventListener("load", adjustAboutWrappers);
  }

  // ------------- Photos -> Modal carousel index -------------
  function initPhotos() {
    document.querySelectorAll("[data-bs-target^='#photoModal']").forEach(img => {
      img.addEventListener("click", function () {
        const modalId = this.getAttribute("data-bs-target");
        const index = +this.getAttribute("data-index");
        const carousel = document.querySelector(modalId + " .carousel");
        const instance = bootstrap.Carousel.getInstance(carousel) || new bootstrap.Carousel(carousel);
        instance.to(index);
      });
    });
  }

  // ------------- Messages -------------
  function renderMessage(list, msg, { prepend = false } = {}) {
    const li = document.createElement("li");
    li.className = "list-group-item d-flex justify-content-between align-items-center";
    li.dataset.id = msg.id;

    const span = document.createElement("span");
    span.className = "msg-text";
    span.textContent = msg.message ?? msg.text ?? msg.content ?? "";

    const actions = document.createElement("div");
    actions.className = "msg-actions d-flex gap-1";

    const editBtn = document.createElement("button");
    editBtn.className = "btn btn-sm btn-outline-secondary edit-btn";
    editBtn.type = "button";
    editBtn.textContent = "✏️";

    const delBtn = document.createElement("button");
    delBtn.className = "btn btn-sm btn-outline-danger delete-btn";
    delBtn.type = "button";
    delBtn.textContent = "🗑️";

    actions.append(editBtn, delBtn);
    li.append(span, actions);
    if (prepend) list.prepend(li); else list.appendChild(li);
  }

  function initMessages() {
    const tg = window.Telegram?.WebApp;
    tg?.ready();
    const USER_ID_FROM_SERVER = document.body.dataset.userId ? Number(document.body.dataset.userId) : null;
    let userId = tg?.initDataUnsafe?.user?.id ?? USER_ID_FROM_SERVER ?? null;

    if (MODE === "DEV" && (userId === null || userId === undefined)) {
    userId = 988269770;
    console.warn("DEV MODE: userId overridden to", userId);
  }

    userId = Number(userId);
    const hasUserId = Number.isInteger(userId) && userId > 0;


    // Load on modal open
    document.querySelectorAll("[id^='messagesModal-']").forEach(modal => {
      modal.addEventListener("show.bs.modal", async function () {
        const specId = this.dataset.specId || this.id.split("-")[1];
        const list = this.querySelector(`#messagesList-${specId}`);
        list.innerHTML = "<li class='list-group-item'>Загрузка...</li>";

        if (!hasUserId) {
        list.innerHTML =
          "<li class='list-group-item text-danger'>Не удалось определить пользователя (user_id). Откройте страницу через Telegram WebApp или авторизуйтесь.</li>";
        return;
      }

        try {


          const url = `/profiles/messages?user_id=${encodeURIComponent(userId)}&specialist_id=${encodeURIComponent(specId)}&_=${Date.now()}`;
          const messages = await fetchJson(url, { cache: "no-store" });
          list.innerHTML = "";
          messages.forEach(m => renderMessage(list, m));
        } catch (err) {
          list.innerHTML = `<li class="list-group-item text-danger">Ошибка загрузки: ${err.message || err}</li>`;
        }
      });
    });

    // Create
    document.querySelectorAll("form[id^='messageForm-']").forEach(form => {
      form.addEventListener("submit", async function (e) {
        e.preventDefault();
        const specId = this.id.split("-")[1];
        const textarea = this.querySelector("textarea");
        const modal = this.closest(".modal");
        const message = textarea.value.trim();
        if (!message) return;

        const caret = getCaretState(textarea);
        try {
          const newMsg = await fetchJson("/profiles/messages", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: Number(userId), specialist_id: Number(specId), message })
          });
          const list = document.querySelector(`#messagesList-${specId}`);
          renderMessage(list, newMsg, { prepend: true });
          textarea.value = "";
        } catch (err) {
          alert("Ошибка: " + err.message);
        } finally {
          afterDom(() => (restoreCaret(caret) || focusComposerIn(modal)));
        }
      });
    });

    // Delegated delete/edit
    document.body.addEventListener("click", async function (e) {
      // Inline confirm delete (no window.confirm)
      if (e.target.classList.contains("delete-btn")) {
        const li = e.target.closest("li");
        const actions = li.querySelector(".msg-actions");
        const modal = e.target.closest(".modal");
        const composer = modal?.querySelector(".modal-footer textarea");
        const caret = getCaretState(composer);

        const old = actions.cloneNode(true);
        const ask = document.createElement("div");
        ask.className = "d-flex gap-1 align-items-center";
        const label = document.createElement("span");
        label.className = "text-danger me-2";
        label.textContent = "Удалить?";

        const yes = document.createElement("button");
        yes.type = "button"; yes.className = "btn btn-sm btn-danger"; yes.textContent = "Удалить";
        const no  = document.createElement("button");
        no.type  = "button"; no.className  = "btn btn-sm btn-secondary"; no.textContent  = "Отмена";

        ask.append(label, yes, no);
        actions.replaceWith(ask);
        afterDom(() => (restoreCaret(caret) || focusComposerIn(modal)));

        no.addEventListener("click", () => {
          ask.replaceWith(old);
          afterDom(() => (restoreCaret(caret) || focusComposerIn(modal)));
        });

        yes.addEventListener("click", async () => {
          try {
            const resp = await fetch(`/profiles/messages/${li.dataset.id}`, { method: "DELETE" });
            if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
            li.remove();
          } catch (err) {
            alert("Ошибка удаления: " + (err.message || err));
            ask.replaceWith(old);
          } finally {
            afterDom(() => (restoreCaret(caret) || focusComposerIn(modal)));
          }
        });
      }

      // Edit
      if (e.target.classList.contains("edit-btn")) {
        const li = e.target.closest("li");
        const msgId = li.dataset.id;
        const textSpan = li.querySelector(".msg-text");
        const oldText = textSpan.textContent;
        const modal = e.target.closest(".modal");

        const textarea = document.createElement("textarea");
        textarea.className = "form-control me-2";
        textarea.value = oldText;

        const saveBtn = document.createElement("button");
        saveBtn.className = "btn btn-sm btn-success me-1"; saveBtn.type = "button"; saveBtn.textContent = "💾";

        const cancelBtn = document.createElement("button");
        cancelBtn.className = "btn btn-sm btn-secondary"; cancelBtn.type = "button"; cancelBtn.textContent = "❌";

        const oldEditBtn = e.target;

        textSpan.replaceWith(textarea);
        oldEditBtn.replaceWith(saveBtn);
        saveBtn.insertAdjacentElement("afterend", cancelBtn);

        textarea.focus();
        try { textarea.setSelectionRange(textarea.value.length, textarea.value.length); } catch {}

        saveBtn.addEventListener("click", async () => {
          const newText = textarea.value.trim();
          if (!newText) return;

          const caret = getCaretState(modal?.querySelector(".modal-footer textarea"));

          try {
            const resp = await fetch(`/profiles/messages/${msgId}`, {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ message: newText })
            });
            if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);

            const newSpan = document.createElement("span");
            newSpan.className = "msg-text";
            newSpan.textContent = newText;
            textarea.replaceWith(newSpan);
            saveBtn.replaceWith(oldEditBtn);
            cancelBtn.remove();
          } catch (err) {
            alert("Ошибка редактирования: " + (err.message || err));
          } finally {
            afterDom(() => (restoreCaret(caret) || focusComposerIn(modal)));
          }
        });

        cancelBtn.addEventListener("click", () => {
          const caret = getCaretState(modal?.querySelector(".modal-footer textarea"));

          const newSpan = document.createElement("span");
          newSpan.className = "msg-text";
          newSpan.textContent = oldText;
          textarea.replaceWith(newSpan);
          saveBtn.replaceWith(oldEditBtn);
          cancelBtn.remove();

          afterDom(() => (restoreCaret(caret) || focusComposerIn(modal)));
        });
      }
    });
  }

  // ------------- Init all on DOM ready -------------
  document.addEventListener("DOMContentLoaded", () => {
    initAbout();
    initPhotos();
    initMessages();
  });
})();
