/**
 * Dependency-free, browser/Node implementation of the adult IBW formulas.
 * Units: centimetres and kilograms, except formula height in inches.
 * This module does not select a medication dosing weight.
 */
const COEFFICIENTS = Object.freeze({
  Devine: { M: [50, 2.3], F: [45.5, 2.3] },
  Robinson: { M: [52, 1.9], F: [49, 1.7] },
  Miller: { M: [56.2, 1.41], F: [53.1, 1.36] },
  Hamwi: { M: [48, 2.7], F: [45.5, 2.2] },
});
const round1 = (value) => Math.round((value + Number.EPSILON) * 10) / 10;
export const poundsToKg = (lbs) => lbs * 0.45359237;
export const inchesToCm = (inches) => inches * 2.54;

export function calculatePatient({ sex, height_cm, weight_kg }) {
  const normalizedSex = String(sex ?? "").trim().toUpperCase();
  const height = Number(height_cm);
  const weight = Number(weight_kg);
  if (!["M", "F"].includes(normalizedSex)) {
    throw new Error("Choose a formula sex coefficient (male or female).");
  }
  if (!Number.isFinite(height) || height < 30 || height > 272) {
    throw new Error("Height must be a finite number between 30 and 272 cm.");
  }
  if (height < 152.4 - 1e-9) {
    throw new Error("These adult formulas are not provided for heights below 152.4 cm (5 ft).");
  }
  if (!Number.isFinite(weight) || weight < 0.5 || weight > 600) {
    throw new Error("Actual weight must be a finite number between 0.5 and 600 kg.");
  }

  const heightInches = height / 2.54;
  const results = Object.fromEntries(
    Object.entries(COEFFICIENTS).map(([name, bySex]) => {
      const [intercept, perInch] = bySex[normalizedSex];
      return [name.toLowerCase(), round1(intercept + perInch * (heightInches - 60))];
    })
  );
  const percent = (weight / results.devine) * 100;
  return {
    sex: normalizedSex,
    height_cm: height,
    height_inches: round1(heightInches),
    actual_weight_kg: round1(weight),
    ...results,
    mean: round1(Object.values(results).reduce((a, b) => a + b, 0) / 4),
    percent_ibw: round1(percent),
    adjusted_bw: percent > 130 ? round1(results.devine + 0.4 * (weight - results.devine)) : null,
  };
}

/** RFC 4180-compatible CSV field parsing, including quoted line breaks and escaped quotes. */
export function parseCsv(source) {
  const text = String(source).replace(/^\uFEFF/, "");
  const rows = [];
  let row = [], field = "", inQuotes = false, afterQuote = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (inQuotes) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (ch === '"') { inQuotes = false; afterQuote = true; }
      else { field += ch; }
    } else if (afterQuote) {
      if (ch === ",") { row.push(field); field = ""; afterQuote = false; }
      else if (ch === "\n" || ch === "\r") {
        row.push(field); rows.push(row); row = []; field = ""; afterQuote = false;
        if (ch === "\r" && text[i + 1] === "\n") i++;
      } else if (ch !== " " && ch !== "\t") {
        throw new Error("Unexpected character after a quoted CSV field.");
      }
    } else if (ch === '"' && field === "") {
      inQuotes = true;
    } else if (ch === ",") {
      row.push(field); field = "";
    } else if (ch === "\n" || ch === "\r") {
      row.push(field); rows.push(row); row = []; field = "";
      if (ch === "\r" && text[i + 1] === "\n") i++;
    } else if (ch === '"') {
      throw new Error("Unexpected quote in an unquoted CSV field.");
    } else {
      field += ch;
    }
  }
  if (inQuotes) throw new Error("Unterminated quoted CSV field.");
  if (afterQuote || field !== "" || row.length > 0) {
    row.push(field); rows.push(row);
  }
  return rows.filter(cells => cells.some(cell => cell.trim() !== ""));
}

const OUTPUT_HEADERS = ["patient_id", "sex", "height_cm", "actual_weight_kg",
  "ibw_devine", "ibw_robinson", "ibw_miller", "ibw_hamwi", "ibw_mean",
  "adjusted_bw", "percent_ibw", "warnings"];

export function processCsvText(text) {
  const parsed = parseCsv(text);
  if (parsed.length < 2) throw new Error("CSV needs a header and at least one data row.");
  const header = parsed[0].map(h => h.trim().toLowerCase());
  for (const name of ["sex", "height_cm", "weight_kg"]) {
    if (!header.includes(name)) throw new Error("Missing required CSV column: " + name);
  }
  if (new Set(header).size !== header.length) throw new Error("Duplicate CSV column names.");
  if (parsed.length > 1001) throw new Error("Maximum 1,000 patient rows per file.");
  const records = parsed.slice(1).map((cells, index) => {
    const data = Object.fromEntries(header.map((name, i) => [name, (cells[i] ?? "").trim()]));
    const id = data.patient_id || "row" + (index + 2);
    try {
      if (cells.length !== header.length) throw new Error("Column count does not match header.");
      const unit = (data.weight_unit || "kg").toLowerCase();
      if (!["kg", "lb", "lbs", "pound", "pounds"].includes(unit)) {
        throw new Error("Unsupported weight unit: " + unit);
      }
      if (data.height_cm === "" || data.weight_kg === "") throw new Error("Missing height or weight.");
      const weight = Number(data.weight_kg);
      const result = calculatePatient({
        sex: data.sex, height_cm: Number(data.height_cm),
        weight_kg: unit === "kg" ? weight : poundsToKg(weight),
      });
      return { id, result, error: "" };
    } catch (error) {
      return { id, result: null, error: error.message };
    }
  });
  return records;
}

function safeCsvField(value) {
  let text = String(value ?? "");
  // Avoid formulas being evaluated when downloaded CSVs are opened in spreadsheets.
  if (/^[\s]*[=+@\-\t\r]/.test(text)) text = "'" + text;
  return '"' + text.replace(/"/g, '""') + '"';
}

export function resultsToCsv(records) {
  const lines = [OUTPUT_HEADERS.map(safeCsvField).join(",")];
  for (const { id, result, error } of records) {
    const values = result ? [
      id, result.sex, result.height_cm, result.actual_weight_kg,
      result.devine, result.robinson, result.miller, result.hamwi, result.mean,
      result.adjusted_bw ?? "", result.percent_ibw, "",
    ] : [id, "", "", "", "", "", "", "", "", "", "", error];
    lines.push(values.map(safeCsvField).join(","));
  }
  return lines.join("\r\n") + "\r\n";
}
