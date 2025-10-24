import { normName, escapeHtml } from "./utils.js";

export function buildSectionHTML(pageName, ticketId, vals = {}) {
  const {
    nameVal = "",
    numVal = "",
    dtVal = "",
    idVal = "",
    checked = false,
  } = vals;
  const checkedAttr = checked ? "checked" : "";
  const showCheckbox = !!(idVal && String(idVal).trim());

  // fragmento para la parte de acciones (checkbox + remover)
  const actionsHTML = `
    <div class="section-actions">
      <label>&nbsp;</label>
      <div class="actions-inner">
        ${
          showCheckbox
            ? `<input autocomplete="off" class="fa-solid fa-check" type="checkbox" title="Permitir Compra" name="section_is_purchase[]" value="${escapeHtml(
                idVal
              )}" ${checkedAttr} />`
            : ""
        }
        <button type="button" class="remove-section fa-solid fa-xmark delete" aria-label="Eliminar Seccion"></button>
      </div>
    </div>
  `;

  if (pageName === "superboletos") {
    return `
      <div class="section-inner">
        <h3 class="section-title">${
          escapeHtml(nameVal) || `Seccion ${ticketId}`
        }</h3>
        <div class="section-row superboletos">
          <div>
            <label class="label">Nombre de la seccion</label>
            <input autocomplete="off" type="text" name="section_name[]" value="${escapeHtml(
              nameVal
            )}" />
          </div>
          <div>
            <label class="label">Numero de tickets</label>
            <input autocomplete="off" type="number" name="num_tickets[]" value="${escapeHtml(
              numVal
            )}" />
          </div>
          <div>
            <label class="label">Fecha y hora</label>
            <input autocomplete="off" type="text" name="event_date_time_tickets[]" class="flat-datetime" value="${escapeHtml(
              dtVal
            )}" />
          </div>
          ${actionsHTML}
        </div>
      </div>
    `;
  }

  // ticketmaster / default
  return `
    <div class="section-inner">
      <h3 class="section-title">${
        escapeHtml(nameVal) || `Seccion ${ticketId}`
      }</h3>
      <div class="section-row default">
        <div>
          <label class="label">Nombre de la seccion</label>
          <input autocomplete="off" type="text" name="section_name[]" value="${escapeHtml(
            nameVal
          )}" />
        </div>
        <div>
          <label class="label">Numero de tickets</label>
          <input autocomplete="off" type="number" name="num_tickets[]" value="${escapeHtml(
            numVal
          )}" />
        </div>
        ${actionsHTML}
      </div>
    </div>
  `;
}

/* Añadir una sección nueva (con animación) */
export function addSection() {
  const container = document.getElementById("sections");
  if (!container) return;

  const count = container.querySelectorAll(".section").length;
  const ticketId = count + 1;
  const pageName =
    document.getElementById("page_name")?.value ||
    document.getElementById("main_filter")?.dataset.value ||
    "ticketmaster";

  const wrapper = document.createElement("div");
  wrapper.className = "section";

  // build with empty vals (new section) -> idVal vacío -> checkbox no se mostrará
  wrapper.innerHTML = buildSectionHTML(pageName, ticketId, {
    nameVal: "",
    numVal: "",
    dtVal: "",
    idVal: "",
    checked: false,
  });
  container.appendChild(wrapper);

  // animate open (replicar comportamiento del index.js original)
  const inner = wrapper.querySelector(".section-inner");
  requestAnimationFrame(() => {
    wrapper.classList.add("enter");
    inner.classList.add("enter");
    inner.style.maxHeight = inner.scrollHeight + "px";
    inner.style.opacity = 1;
    inner.style.transform = "translateY(0)";
  });
  inner.addEventListener("transitionend", function _t(e) {
    if (e.propertyName === "max-height") {
      inner.style.maxHeight = "";
      inner.style.opacity = "";
      inner.style.transform = "";
      inner.removeEventListener("transitionend", _t);
    }
  });

  attachSectionListeners(wrapper);
  refreshSectionTitles();
}

/* Remove con animación */
export function removeSection(btn) {
  const sec = btn.closest(".section");
  if (!sec) return;
  const inner = sec.querySelector(".section-inner");
  inner.style.maxHeight = inner.scrollHeight + "px";
  requestAnimationFrame(() => {
    sec.classList.add("exit");
    inner.style.maxHeight = "0px";
    inner.style.opacity = 0;
    inner.style.transform = "translateY(-8px)";
  });
  inner.addEventListener("transitionend", function _te(e) {
    if (e.propertyName === "max-height") {
      sec.remove();
      refreshSectionTitles();
      inner.removeEventListener("transitionend", _te);
    }
  });
}

/* Attach listeners comunes */
export function attachSectionListeners(section) {
  if (!section) return;

  // remove buttons
  section.querySelectorAll(".remove-section").forEach((btn) => {
    if (!btn._bound) {
      btn.addEventListener("click", () => removeSection(btn));
      btn._bound = true;
    }
  });

  // name inputs -> actualizar titulos en input
  section.querySelectorAll('input[name="section_name[]"]').forEach((input) => {
    if (!input._bound) {
      input.addEventListener("input", refreshSectionTitles);
      input._bound = true;
    }
  });

  // flatpickr inicializar si existe campo
  const fd = section.querySelector(".flat-datetime");
  if (fd && typeof flatpickr === "function") {
    if (!fd._flatInit) {
      flatpickr(fd, {
        enableTime: true,
        dateFormat: "Y-m-d\\TH:i",
        time_24hr: true,
        allowInput: true,
      });
      fd._flatInit = true;
    }
  }
}

/* Titulos: números y duplicados */
export function refreshSectionTitles() {
  const sections = Array.from(document.querySelectorAll("#sections .section"));
  const seen = {};
  sections.forEach((sec, i) => {
    const name =
      sec.querySelector('input[name="section_name[]"]')?.value.trim() || "";
    const key = normName(name || `sec-${i}`);
    seen[key] = (seen[key] || 0) + 1;
    const title = name ? `Seccion ${name}` : `Seccion ${i + 1}`;
    const titleText = seen[key] > 1 ? `${title} (${seen[key]})` : title;
    const titleEl = sec.querySelector(".section-title");
    if (titleEl) titleEl.textContent = titleText;
  });
}

/* Rebuild / preservar valores antes de transformar cada sección */
export function updateSectionsForPage(pageName) {
  document.querySelectorAll("#sections .section").forEach((sec, i) => {
    const vals = {
      nameVal: sec.querySelector('input[name="section_name[]"]')?.value || "",
      numVal: sec.querySelector('input[name="num_tickets[]"]')?.value || "",
      dtVal:
        sec.querySelector('input[name="event_date_time_tickets[]"]')?.value ||
        "",
      // preservar checkbox value y checked si existe (edit template)
      idVal:
        sec.querySelector('input[name="section_is_purchase[]"]')?.value || "",
      checked: !!sec.querySelector('input[name="section_is_purchase[]"]')
        ?.checked,
    };
    // reemplaza interior y reaplica listeners
    sec.innerHTML = buildSectionHTML(pageName, i + 1, vals);
    attachSectionListeners(sec);
  });
  refreshSectionTitles();
}
