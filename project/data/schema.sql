PRAGMA foreign_keys = ON;
CREATE TABLE unit (unit_id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL UNIQUE, city TEXT NOT NULL) STRICT;
CREATE TABLE specialty (specialty_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE) STRICT;
CREATE TABLE doctor (doctor_id INTEGER PRIMARY KEY, name TEXT NOT NULL, registration TEXT NOT NULL UNIQUE) STRICT;
CREATE TABLE doctor_specialty (
 doctor_id INTEGER NOT NULL REFERENCES doctor(doctor_id), specialty_id INTEGER NOT NULL REFERENCES specialty(specialty_id),
 PRIMARY KEY(doctor_id,specialty_id)) STRICT;
CREATE TABLE patient (patient_id INTEGER PRIMARY KEY, name TEXT NOT NULL, fictional_code TEXT NOT NULL UNIQUE) STRICT;
CREATE TABLE surgical_procedure (
 procedure_id INTEGER PRIMARY KEY, specialty_id INTEGER NOT NULL REFERENCES specialty(specialty_id), name TEXT NOT NULL UNIQUE) STRICT;
CREATE TABLE item (
 item_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
 category TEXT NOT NULL CHECK(category IN ('equipa','sala','material','medicamento','protese')),
 unit TEXT NOT NULL, unit_cost_cents INTEGER NOT NULL CHECK(unit_cost_cents >= 0)) STRICT;
CREATE TABLE package (
 unit_id INTEGER NOT NULL REFERENCES unit(unit_id),
 package_id INTEGER PRIMARY KEY, procedure_id INTEGER NOT NULL REFERENCES surgical_procedure(procedure_id),
 name TEXT NOT NULL, sale_price_cents INTEGER NOT NULL CHECK(sale_price_cents >= 0)) STRICT;
CREATE TABLE package_item (
 package_id INTEGER NOT NULL REFERENCES package(package_id), item_id INTEGER NOT NULL REFERENCES item(item_id),
 quantity REAL NOT NULL CHECK(quantity > 0 AND quantity <= 1000000 AND ABS(quantity*1000-ROUND(quantity*1000)) < 0.000001), PRIMARY KEY(package_id,item_id)) STRICT;
CREATE TABLE surgery (
 unit_id INTEGER NOT NULL REFERENCES unit(unit_id),
 surgery_id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES patient(patient_id),
 procedure_id INTEGER NOT NULL REFERENCES surgical_procedure(procedure_id), scheduled_at TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('agendada','em_curso','concluida','cancelada'))) STRICT;
CREATE TABLE surgery_doctor (
 surgery_id INTEGER NOT NULL REFERENCES surgery(surgery_id), doctor_id INTEGER NOT NULL REFERENCES doctor(doctor_id),
 role TEXT NOT NULL, PRIMARY KEY(surgery_id,doctor_id)) STRICT;
CREATE TABLE budget (
 modality TEXT NOT NULL CHECK(modality IN ('avulso','pacote')),
 package_id INTEGER REFERENCES package(package_id),
 budget_id INTEGER PRIMARY KEY, surgery_id INTEGER NOT NULL REFERENCES surgery(surgery_id),
 version INTEGER NOT NULL CHECK(version > 0),
 status TEXT NOT NULL CHECK(status IN ('rascunho','aprovado','substituido')),
 sale_price_cents INTEGER NOT NULL CHECK(sale_price_cents >= 0), UNIQUE(surgery_id,version), CHECK((modality='pacote' AND package_id IS NOT NULL) OR (modality='avulso' AND package_id IS NULL))) STRICT;
CREATE UNIQUE INDEX one_approved_budget ON budget(surgery_id) WHERE status='aprovado';
CREATE TABLE budget_line (
 budget_id INTEGER NOT NULL REFERENCES budget(budget_id), item_id INTEGER NOT NULL REFERENCES item(item_id),
 quantity REAL NOT NULL CHECK(quantity > 0 AND quantity <= 1000000 AND ABS(quantity*1000-ROUND(quantity*1000)) < 0.000001), unit_cost_cents INTEGER NOT NULL CHECK(unit_cost_cents >= 0),
 PRIMARY KEY(budget_id,item_id)) STRICT;
CREATE TABLE consumption (
 consumption_id INTEGER PRIMARY KEY, surgery_id INTEGER NOT NULL REFERENCES surgery(surgery_id),
 item_id INTEGER NOT NULL REFERENCES item(item_id), quantity REAL NOT NULL CHECK(quantity > 0 AND quantity <= 1000000 AND ABS(quantity*1000-ROUND(quantity*1000)) < 0.000001),
 unit_cost_cents INTEGER NOT NULL CHECK(unit_cost_cents >= 0), reason TEXT,
 recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP) STRICT;
CREATE INDEX consumption_surgery ON consumption(surgery_id);
CREATE INDEX surgery_date ON surgery(scheduled_at);

-- Preço de venda de referência, separado dos custos e dos orçamentos históricos.
CREATE TABLE procedure_pricing (
 procedure_id INTEGER PRIMARY KEY REFERENCES surgical_procedure(procedure_id),
 pricing_model TEXT NOT NULL CHECK(pricing_model IN ('fechado','estimado')),
 reference_price_cents INTEGER CHECK(reference_price_cents > 0),
 price_origin TEXT NOT NULL CHECK(price_origin IN ('simulado','por_definir')),
 country TEXT NOT NULL DEFAULT 'PT' CHECK(country='PT'),
 currency TEXT NOT NULL DEFAULT 'EUR' CHECK(currency='EUR'),
 notes TEXT NOT NULL,
 CHECK((price_origin='por_definir' AND reference_price_cents IS NULL)
    OR (price_origin='simulado' AND reference_price_cents IS NOT NULL))
) STRICT;

CREATE TABLE doctor_unit (
 doctor_id INTEGER NOT NULL REFERENCES doctor(doctor_id), unit_id INTEGER NOT NULL REFERENCES unit(unit_id),
 PRIMARY KEY(doctor_id,unit_id)) STRICT;
CREATE TABLE unit_procedure_price (
 unit_id INTEGER NOT NULL REFERENCES unit(unit_id), procedure_id INTEGER NOT NULL REFERENCES surgical_procedure(procedure_id),
 sale_price_cents INTEGER NOT NULL CHECK(sale_price_cents>0),
 PRIMARY KEY(unit_id,procedure_id)) STRICT;
CREATE INDEX surgery_unit_date ON surgery(unit_id,scheduled_at);
