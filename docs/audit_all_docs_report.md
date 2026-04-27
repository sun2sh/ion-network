# Doc audit report — every doc in docs/ vs beckn.yaml

Each doc's JSON blocks were parsed and every Beckn-named object inside them 
was validated against `beckn.yaml`'s schema. Two checks per object:
- Every key on the object is one Beckn defines for that type
- Every Beckn-required property is present

Plus a check on `*Attributes` bags (must have `@context` and `@type`).


| Doc | JSON blocks | Parse errors | Issues |
|---|---:|---:|---:|
| `ION_Beckn_Conformance.md` | 0 | 0 | 0 |
| `ION_Council_Open_Questions.md` | 0 | 0 | 0 |
| `ION_Developer_Orientation.md` | 3 | 0 | 0 |
| `ION_First_Transaction.md` | 13 | 0 | 0 |
| `ION_Glossary.md` | 0 | 0 | 0 |
| `ION_Layer_Model.md` | 0 | 0 | 0 |
| `ION_Onboarding_and_Auth.md` | 2 | 0 | 0 |
| `ION_Schema_Style_Guide.md` | 0 | 0 | 0 |
| `ION_Sector_A_Trade.md` | 1 | 0 | 0 |
| `ION_Sector_B_Logistics.md` | 6 | 0 | 0 |
| `ION_Semantic_Model_Transition.md` | 0 | 0 | 0 |
| `ION_Start_Here.md` | 0 | 0 | 0 |
| **TOTAL** | **25** | **0** | **0** |

