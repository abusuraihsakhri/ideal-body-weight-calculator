import test from "node:test";
import assert from "node:assert/strict";
import { calculatePatient, inchesToCm, poundsToKg, parseCsv, processCsvText, resultsToCsv } from "../web/calculator.mjs";

test("Devine, Robinson, Miller, Hamwi agree with published reference cases", () => {
  const male = calculatePatient({ sex: "M", height_cm: inchesToCm(70), weight_kg: 80 });
  assert.deepEqual([male.devine, male.robinson, male.miller, male.hamwi], [73, 71, 70.3, 75]);
  const female = calculatePatient({ sex: "F", height_cm: inchesToCm(64), weight_kg: 60 });
  assert.deepEqual([female.devine, female.robinson, female.miller, female.hamwi], [54.7, 55.8, 58.5, 54.3]);
});

test("adjusted body weight is conditional, never a dosing instruction", () => {
  const normal = calculatePatient({ sex: "M", height_cm: inchesToCm(70), weight_kg: 80 });
  assert.equal(normal.adjusted_bw, null);
  const elevated = calculatePatient({ sex: "M", height_cm: inchesToCm(70), weight_kg: 110 });
  assert.equal(elevated.adjusted_bw, 87.8);
  assert.equal(elevated.percent_ibw, 150.7);
});

test("pounds conversion, height boundaries, finite inputs and sex validation", () => {
  assert.ok(Math.abs(poundsToKg(154) - 69.8532) < 0.001);
  assert.equal(calculatePatient({ sex: "F", height_cm: 152.4, weight_kg: 50 }).devine, 45.5);
  for (const bad of [NaN, Infinity, -Infinity, 0, 300, 150]) {
    assert.throws(() => calculatePatient({ sex: "M", height_cm: bad, weight_kg: 80 }));
  }
  for (const bad of [NaN, Infinity, 0, -30, 601]) {
    assert.throws(() => calculatePatient({ sex: "M", height_cm: 175, weight_kg: bad }));
  }
  assert.throws(() => calculatePatient({ sex: "X", height_cm: 175, weight_kg: 80 }));
});

test("CSV parser supports BOM, line breaks and quoted text", () => {
  assert.deepEqual(parseCsv("\uFEFFa,b\r\n\"hello, world\",\"two\nlines\"\r\n"),
    [["a", "b"], ["hello, world", "two\nlines"]]);
  assert.throws(() => parseCsv('a,b\n"unfinished'));
  assert.throws(() => parseCsv('a,b\n"x"y,z'));
});

test("batch input validates per row and exports safely", () => {
  const csv = "patient_id,sex,height_cm,weight_kg,weight_unit\n" +
    "case01,M,177.8,80,kg\n" +
    "=1+2,F,163,130,lb\n" +
    "bad,M,150,70,kg\n" +
    "wrong-unit,F,163,55,stone\n";
  const rows = processCsvText(csv);
  assert.equal(rows.length, 4);
  assert.equal(rows.filter(r => r.result).length, 2);
  assert.equal(rows[0].result.devine, 73);
  assert.ok(rows[1].result.actual_weight_kg > 58.9);
  assert.match(rows[2].error, /below 152.4/);
  assert.match(rows[3].error, /Unsupported weight unit/);
  const output = resultsToCsv(rows);
  assert.match(output, /'=1\+2/);
  assert.match(output, /wrong-unit/);
  assert.deepEqual(parseCsv(output)[0][0], "patient_id");
});

test("CSV rejects missing and duplicate headers and oversized input", () => {
  assert.throws(() => processCsvText("sex,height_cm\nM,175"), /weight_kg/);
  assert.throws(() => processCsvText("sex,sex,height_cm,weight_kg\nM,M,175,80"), /Duplicate/);
  assert.throws(() => processCsvText("sex,height_cm,weight_kg\n" + "M,175,80\n".repeat(1001)), /Maximum/);
});
