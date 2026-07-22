Column Definitions Schema
=========================

This document describes the JSON schema used to validate **column definition** files.
A column definition file is a JSON array where each element describes one datastore
field, pairing its column name with human-readable metadata.

Purpose
-------

The schema enforces that every column definition provides:

- a **column name** (``field``) as it appears in the CSV file,
- a **human-readable label** (``label``) for display, and
- a **description** (``description``) explaining the column's meaning.

Validating against this schema catches missing fields and empty values before the
definitions are consumed downstream.

Example document
----------------

.. code-block:: json

   [
     { "field": "col_name", "label": "Column Label", "description": "Human-readable description." },
     { "field": "another_col", "label": "Another Label", "description": "Second column description." }
   ]

The schema
----------

.. note::

   The runtime validator uses an embedded copy of this schema in
   ``ckanext-hdx_package/ckanext/hdx_package/helpers/custom_validator.py``. Keep this document in sync with it.

.. code-block:: json

   {
     "$schema": "https://json-schema.org/draft/2020-12/schema",
     "$id": "https://data.humdata.org/schemas/column-definitions.json",
     "title": "Column Definitions",
     "description": "A list of column definitions describing datastore fields.",
     "type": "array",
     "minItems": 1,
     "items": {
       "type": "object",
       "examples": [
         {
           "field": "col_name",
           "label": "Column Label",
           "description": "Human-readable description."
         }
       ],
       "properties": {
         "field": {
           "type": "string",
           "description": "Column name from csv file",
           "minLength": 1
         },
         "label": {
           "type": "string",
           "description": "Human-readable column label.",
           "minLength": 1
         },
         "description": {
           "type": "string",
           "description": "Human-readable description of the column.",
           "minLength": 1
         }
       },
       "required": ["field", "label", "description"],
       "additionalProperties": true
     }
   }

Field reference
---------------

.. list-table::
   :header-rows: 1
   :widths: 15 10 10 15 50

   * - Field
     - Type
     - Required
     - Constraints
     - Notes
   * - ``field``
     - string
     - Yes
     - Non-empty
     - Column name from the CSV file. Any non-empty string is accepted.
   * - ``label``
     - string
     - Yes
     - Non-empty
     - Human-readable label used for display.
   * - ``description``
     - string
     - Yes
     - Non-empty
     - Human-readable explanation of what the column contains.

Validation rules
----------------

- **Top level must be an array.** A single object or any other type fails validation.
- **At least one item** is required (``minItems: 1``). Remove this constraint to permit
  an empty list.
- **Each item is an object** with the three required properties above.
- **All three properties are mandatory.** Omitting any of ``field``, ``label``, or
  ``description`` fails validation.
- **No empty strings.** ``minLength: 1`` rejects ``""`` for every property.
- **Extra properties are allowed** (``additionalProperties: true`` — also the
  Draft 2020-12 default, stated explicitly here for clarity), so you can attach keys
  such as ``type``, ``unit``, or ``hxl_tag`` without failing validation. Set this to
  ``false`` to reject anything beyond the three defined properties.
- **The** ``examples`` **keyword** on ``items`` is annotation-only — it never affects
  validation, but editors and tooling surface it to make the schema self-documenting.

A note on uniqueness
~~~~~~~~~~~~~~~~~~~~

JSON Schema's ``uniqueItems`` compares whole objects, so it will **not** enforce that
``field`` values are unique across the array. If you need unique field names, enforce
that in application code after schema validation passes:

.. code-block:: python

   from collections import Counter

   counts = Counter(item["field"] for item in data)
   dupes = [name for name, n in counts.items() if n > 1]
   if dupes:
       raise ValueError(f"Duplicate field names: {dupes}")

Validating
----------

Python (``jsonschema``)
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import json
   from jsonschema import Draft202012Validator

   with open("column-definitions.schema.json") as f:
       schema = json.load(f)
   with open("columns.json") as f:
       data = json.load(f)

   validator = Draft202012Validator(schema)
   errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
   if errors:
       for e in errors:
           loc = "/".join(str(p) for p in e.path) or "(root)"
           print(f"{loc}: {e.message}")
   else:
       print("Valid.")

JavaScript / Node (``ajv``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: javascript

   import Ajv2020 from "ajv/dist/2020.js";
   import { readFileSync } from "fs";

   const schema = JSON.parse(readFileSync("./column-definitions.schema.json", "utf8"));
   const data   = JSON.parse(readFileSync("./columns.json", "utf8"));

   const ajv = new Ajv2020({ allErrors: true });
   const validate = ajv.compile(schema);

   if (validate(data)) {
     console.log("Valid.");
   } else {
     for (const err of validate.errors) {
       console.log(`${err.instancePath || "(root)"}: ${err.message}`);
     }
   }

.. note::

   Reading the files with ``readFileSync`` + ``JSON.parse`` avoids version-specific
   JSON-import syntax. If you prefer JSON import attributes, use
   ``with { type: "json" }`` (Node 22+); the older ``assert { type: "json" }`` form
   was deprecated in Node 20 and removed in Node 22.

Customization quick reference
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Goal
     - Change
   * - Reject unknown keys
     - Set ``additionalProperties`` to ``false``
   * - Allow an empty list
     - Remove ``minItems: 1``
   * - Restrict ``field`` to safe identifiers
     - Add ``"pattern": "^[a-zA-Z_][a-zA-Z0-9_]*$"`` to ``field``
   * - Cap ``field`` length
     - Add ``"maxLength": 63`` to ``field``
   * - Require a fixed vocabulary of fields
     - Add an ``enum`` to ``field``
   * - Add an optional typed attribute
     - Add it under ``properties`` (leave it out of ``required``)
