import { updateSectionsForPage } from "./sections.js";

// reemplazar toda la función setupFilter por esta (filter.js)
export function setupFilter() {
  const wrap = document.getElementById("main_filter");
  if (!wrap) return;

  const toggle = wrap.querySelector(".filter-toggle");
  const list = wrap.querySelector(".filter-list");
  const label = wrap.querySelector(".label");
  const pageName = document.getElementById("page_name");

  console.log(wrap);
  function filterTickets() {
    const mainPage = wrap.dataset.value || (pageName ? pageName.value : "");
    const rowsIngresados = document.querySelectorAll("#uncompleted tbody tr");
    const rowsCompletados = document.querySelectorAll("#completed tbody tr");
    const applyFilter = (rows) => {
      rows.forEach((row) => {
        const page = (row.getAttribute("data-page") || "").toString();
        row.style.display =
          !mainPage || mainPage === "" || page === mainPage ? "" : "none";
      });
    };
    applyFilter(rowsIngresados);
    applyFilter(rowsCompletados);
  }

  // abrir/cerrar toggle
  toggle.addEventListener("click", (e) => {
    e.stopPropagation();
    const opening = !wrap.classList.contains("open");
    wrap.classList.toggle("open", opening);
    list.setAttribute("aria-hidden", String(!opening));
  });

  // cerrar al click fuera
  document.addEventListener("click", (e) => {
    if (!wrap.contains(e.target)) {
      wrap.classList.remove("open");
      list.setAttribute("aria-hidden", "true");
    }
  });

  // seleccionar opcion
  list.addEventListener("click", (e) => {
    const li = e.target.closest("li");
    if (!li) return;
    list.querySelectorAll("li").forEach((x) => x.classList.remove("active"));
    li.classList.add("active");

    const val = li.dataset.value || "";
    wrap.dataset.value = val;

    if (label) label.textContent = li.textContent.trim();

    // actualizar ambos pageName (si existen) y despachar evento change
    if (pageName) {
      pageName.value = val;
      pageName.dispatchEvent(new Event("change", { bubbles: true }));
    }

    // cerrar visualmente
    wrap.classList.remove("open");
    list.setAttribute("aria-hidden", "true");

    // reactividad
    updateSectionsForPage(val);
    filterTickets();
  });

  // keyboard navigation
  list.addEventListener("keydown", (e) => {
    const items = Array.from(list.querySelectorAll("li"));
    const idx = items.indexOf(document.activeElement);
    if (e.key === "ArrowDown") {
      e.preventDefault();
      items[(idx + 1) % items.length].focus();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      items[(idx - 1 + items.length) % items.length].focus();
    } else if (e.key === "Enter") {
      document.activeElement.click();
    }
  });

  // inicializar desde dataset / pageName si hay valor
  const initial = wrap.dataset.value || (pageName ? pageName.value : "");
  if (initial) {
    wrap.dataset.value = initial;
    const li = wrap.querySelector(`.filter-list li[data-value="${initial}"]`);
    if (li) {
      li.classList.add("active");
      if (label) label.textContent = li.textContent.trim();
    } else {
      if (label)
        label.textContent = initial.charAt(0).toUpperCase() + initial.slice(1);
    }
    // sincronizar pageName(s) si no coinciden ya
    if (pageName && pageName.value !== initial) {
      pageName.value = initial;
      pageName.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }

  // reaccionar si alguno de los pageName cambia por otro script
  [pageName].forEach((h) => {
    if (!h) return;
    h.addEventListener("change", function () {
      const val = this.value || "";
      wrap.dataset.value = val;
      updateSectionsForPage(val);
      filterTickets();

      // actualizar estado visual de la lista y label
      list.querySelectorAll("li").forEach((x) => x.classList.remove("active"));
      const newLi = wrap.querySelector(`.filter-list li[data-value="${val}"]`);
      if (newLi) {
        newLi.classList.add("active");
        if (label) label.textContent = newLi.textContent.trim();
      } else {
        if (label)
          label.textContent = val
            ? val.charAt(0).toUpperCase() + val.slice(1)
            : "Paginas";
      }
    });
  });

  // aplicar filtro inicial
  filterTickets();
}
