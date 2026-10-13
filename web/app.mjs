import { calculatePatient, poundsToKg, inchesToCm, processCsvText, resultsToCsv } from "./calculator.mjs";

const byId = id => document.getElementById(id);
const formatKg = value => Number(value).toFixed(1) + " kg";
const form = byId("patient-form");
const message = byId("form-message");
const output = byId("patient-results");
const batchMessage = byId("batch-message");
const download = byId("download-csv");
let batchRecords = [];

function displayCalculation() {
  message.textContent = "";
  output.hidden = true;
  try {
    const heightInput = byId("height").value.trim();
    const weightInput = byId("weight").value.trim();
    if (!heightInput || !weightInput) throw new Error("Enter both height and actual weight.");
    const heightRaw = Number(heightInput);
    const weightRaw = Number(weightInput);
    if (!Number.isFinite(heightRaw) || !Number.isFinite(weightRaw)) {
      throw new Error("Enter finite numeric values.");
    }
    const height = byId("height-unit").value === "in" ? inchesToCm(heightRaw) : heightRaw;
    const weight = byId("weight-unit").value === "lb" ? poundsToKg(weightRaw) : weightRaw;
    const result = calculatePatient({ sex: byId("sex").value, height_cm: height, weight_kg: weight });
    for (const name of ["devine", "robinson", "miller", "hamwi", "mean"]) {
      byId("result-" + name).textContent = formatKg(result[name]);
    }
    byId("result-height").textContent = result.height_inches.toFixed(1) + " in";
    byId("result-percent").textContent = result.percent_ibw.toFixed(1) + "%";
    byId("result-adjusted").textContent =
      result.adjusted_bw === null ? "Not shown (≤130% Devine IBW)" : formatKg(result.adjusted_bw);
    byId("result-note").textContent = result.adjusted_bw === null
      ? "Adjusted body weight is displayed only above 130% of Devine IBW, matching the Python workflow."
      : "Adjusted body weight = Devine IBW + 0.4 × (actual weight − Devine IBW). This is not a dosing directive.";
    output.hidden = false;
  } catch (error) {
    message.textContent = error.message;
  }
}

form.addEventListener("submit", event => {
  event.preventDefault();
  displayCalculation();
});

byId("reset-form").addEventListener("click", () => {
  form.reset();
  output.hidden = true;
  message.textContent = "";
  byId("height").focus();
});

byId("batch-form").addEventListener("submit", async event => {
  event.preventDefault();
  batchMessage.textContent = "";
  download.disabled = true;
  batchRecords = [];
  const file = byId("csv-file").files[0];
  if (!file) { batchMessage.textContent = "Choose a CSV file."; return; }
  if (file.size > 2 * 1024 * 1024) {
    batchMessage.textContent = "File must be 2 MB or smaller.";
    return;
  }
  try {
    batchRecords = processCsvText(await file.text());
    const count = batchRecords.filter(r => r.result !== null).length;
    batchMessage.textContent = count + " calculated; " +
      (batchRecords.length - count) + " row(s) with validation errors. Download results for details.";
    download.disabled = false;
  } catch (error) {
    batchMessage.textContent = error.message;
  }
});

download.addEventListener("click", () => {
  if (!batchRecords.length) return;
  const blob = new Blob([resultsToCsv(batchRecords)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "ibw-results.csv";
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

displayCalculation();
