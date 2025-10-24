export function normName(s) {
  return (s || "").trim().toLowerCase();
}

export function format24To12(time24) {
  if (!time24) return "";
  const [hStr, m] = time24.split(":");
  let h = parseInt(hStr, 10);
  const ampm = h >= 12 ? "pm" : "am";
  h = ((h + 11) % 12) + 1;
  return `${h}:${m}${ampm}`;
}

export const monthMap = {
  Jan: "Enero",
  Feb: "Febrero",
  Mar: "Marzo",
  Apr: "Abril",
  May: "Mayo",
  Jun: "Junio",
  Jul: "Julio",
  Aug: "Agosto",
  Sep: "Septiembre",
  Oct: "Octubre",
  Nov: "Noviembre",
  Dec: "Diciembre",
  Ene: "Enero",
  Abr: "Abril",
  Dic: "Diciembre",
};

export function escapeHtml(str) {
  if (str === undefined || str === null) return "";
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
