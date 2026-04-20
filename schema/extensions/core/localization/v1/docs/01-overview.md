# ION Localization Extension — Overview

Multilingual text objects for all catalog content. Keys are ISO 639-1 language codes.

## The LocalisedText pattern
```json
{ "id": "Nasi Goreng Spesial", "en": "Special Fried Rice" }
```
`id` (Bahasa Indonesia) is **always mandatory** — ION Network Policy requires all catalog content to have Bahasa Indonesia text. This is enforced at catalog publish validation.

## English requirement
`en` is mandatory only for the XB (cross-border export) commerce pattern. For all domestic patterns, English is optional but recommended.

## Applies to
`name`, `shortDesc`, `longDesc` on resources and providers. Also used inside customisationGroups (group name, option labels) and menuCategory names.
