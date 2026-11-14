# ERD da versão 1.0

```mermaid
erDiagram
 specialty ||--o{ doctor_specialty : specialty_id
 doctor ||--o{ doctor_specialty : doctor_id
 specialty ||--o{ surgical_procedure : specialty_id
 surgical_procedure ||--o{ package : procedure_id
 unit ||--o{ package : unit_id
 item ||--o{ package_item : item_id
 package ||--o{ package_item : package_id
 surgical_procedure ||--o{ surgery : procedure_id
 patient ||--o{ surgery : patient_id
 unit ||--o{ surgery : unit_id
 doctor ||--o{ surgery_doctor : doctor_id
 surgery ||--o{ surgery_doctor : surgery_id
 surgery ||--o{ budget : surgery_id
 package o|--o{ budget : package_id
 item ||--o{ budget_line : item_id
 budget ||--o{ budget_line : budget_id
 item ||--o{ consumption : item_id
 surgery ||--o{ consumption : surgery_id
 surgical_procedure ||--o| procedure_pricing : procedure_id
 unit ||--o{ doctor_unit : unit_id
 doctor ||--o{ doctor_unit : doctor_id
 surgical_procedure ||--o{ unit_procedure_price : procedure_id
 unit ||--o{ unit_procedure_price : unit_id
 unit {
  INTEGER unit_id PK
  TEXT code
  TEXT name
  TEXT city
 }
 specialty {
  INTEGER specialty_id PK
  TEXT name
 }
 doctor {
  INTEGER doctor_id PK
  TEXT name
  TEXT registration
 }
 doctor_specialty {
  INTEGER doctor_id PK,FK
  INTEGER specialty_id PK,FK
 }
 patient {
  INTEGER patient_id PK
  TEXT name
  TEXT fictional_code
 }
 surgical_procedure {
  INTEGER procedure_id PK
  INTEGER specialty_id FK
  TEXT name
 }
 item {
  INTEGER item_id PK
  TEXT name
  TEXT category
  TEXT unit
  INTEGER unit_cost_cents
 }
 package {
  INTEGER unit_id FK
  INTEGER package_id PK
  INTEGER procedure_id FK
  TEXT name
  INTEGER sale_price_cents
 }
 package_item {
  INTEGER package_id PK,FK
  INTEGER item_id PK,FK
  REAL quantity
 }
 surgery {
  INTEGER unit_id FK
  INTEGER surgery_id PK
  INTEGER patient_id FK
  INTEGER procedure_id FK
  TEXT scheduled_at
  TEXT status
 }
 surgery_doctor {
  INTEGER surgery_id PK,FK
  INTEGER doctor_id PK,FK
  TEXT role
 }
 budget {
  TEXT modality
  INTEGER package_id FK
  INTEGER budget_id PK
  INTEGER surgery_id FK
  INTEGER version
  TEXT status
  INTEGER sale_price_cents
 }
 budget_line {
  INTEGER budget_id PK,FK
  INTEGER item_id PK,FK
  REAL quantity
  INTEGER unit_cost_cents
 }
 consumption {
  INTEGER consumption_id PK
  INTEGER surgery_id FK
  INTEGER item_id FK
  REAL quantity
  INTEGER unit_cost_cents
  TEXT reason
  TEXT recorded_at
 }
 procedure_pricing {
  INTEGER procedure_id PK,FK
  TEXT pricing_model
  INTEGER reference_price_cents
  TEXT price_origin
  TEXT country
  TEXT currency
  TEXT notes
 }
 doctor_unit {
  INTEGER doctor_id PK,FK
  INTEGER unit_id PK,FK
 }
 unit_procedure_price {
  INTEGER unit_id PK,FK
  INTEGER procedure_id PK,FK
  INTEGER sale_price_cents
 }
```

Cardinalidades referem-se à estrutura. Aprovação exige linhas, e conclusão exige cirurgião e consumo, por triggers. Um episódio pode ter zero orçamentos no DDL; o serviço cria sempre um orçamento atomicamente. package_id em budget é opcional apenas na modalidade avulso. Quantidades e snapshots pertencem à associação/operação, não ao catálogo.
