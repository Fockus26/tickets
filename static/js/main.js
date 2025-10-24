// main.js
import { setupFilter } from "./filter.js";
import {
  addSection,
  updateSectionsForPage,
  refreshSectionTitles,
} from "./sections.js";
import { monthMap, format24To12 } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  // inicializar filtro (si existe)
  setupFilter();

  // actualizar títulos de secciones ya existentes
  refreshSectionTitles();

  // conectar botón añadir sección (por id o por clase fallback)
  const addBtn =
    document.getElementById("add_section_btn") ||
    document.querySelector(".floating-button.fa-plus");
  if (addBtn) addBtn.addEventListener("click", addSection);

  // formatear tabla (mes/hora)
  document
    .querySelectorAll("#uncompleted tbody tr, #completed tbody tr")
    .forEach((tr) => {
      const cells = tr.querySelectorAll("td");
      if (cells.length < 7) return;
      const monthCell = cells[4];
      const timeCell = cells[6];
      if (monthCell) {
        const txt = monthCell.textContent.trim();
        monthCell.textContent =
          monthMap[txt] || monthMap[txt.slice(0, 3)] || txt;
      }
      if (timeCell) {
        timeCell.textContent = format24To12(timeCell.textContent.trim());
      }
    });

  // inicializar flatpickr principal si está presente
  const range = document.getElementById("event_date_range");
  console.log(range);
  if (range && typeof flatpickr === "function") {
    flatpickr(range, {
      mode: "range",
      enableTime: true,
      dateFormat: "Y-m-d\\TH:i",
      time_24hr: true,
      allowInput: true,
    });
  }

  // sincronizar page_name -> actualizar secciones al cargar y cuando cambie
  const pageName = document.getElementById("page_name");
  if (pageName) {
    pageName.addEventListener("change", () =>
      updateSectionsForPage(pageName.value || "ticketmaster")
    );
    // llamar una vez con el valor actual
    updateSectionsForPage(pageName.value || "ticketmaster");
  } else {
    // fallback: si no existe pageName, usa data-page del body o del filtro
    const bodyPage = document.body.dataset.page;
    updateSectionsForPage(bodyPage || "ticketmaster");
  }
});
