import json
from collections import defaultdict

import pytest

from ckan.lib.navl.dictization_functions import StopOnError
from ckanext.hdx_package.helpers.custom_validator import hdx_validate_data_dictionary

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

KEY = ("hdx_data_dictionary",)


def _run(value):
    """
    Run the validator with a single field value and return (data, errors).

    ``data``   – the dict passed to the validator (may be mutated).
    ``errors`` – defaultdict(list) with accumulated error messages.
    """
    data = {KEY: value}
    errors = defaultdict(list)
    hdx_validate_data_dictionary(KEY, data, errors, context={})
    return data, errors


# ---------------------------------------------------------------------------
# Valid inputs
# ---------------------------------------------------------------------------


class TestHdxValidateDataDictionaryValid:
    def test_valid_list(self):
        """A well-formed list is accepted and persisted as a JSON string."""
        payload = [
            {"field": "col_name", "label": "Column Label", "description": "Desc."},
            {"field": "another_col", "label": "Another", "description": "Second."},
        ]
        data, errors = _run(payload)
        assert not errors[KEY]
        assert data[KEY] == json.dumps(payload)

    def test_valid_json_string(self):
        """A JSON string encoding a valid array is accepted."""
        payload = [{"field": "my_col", "label": "My Col", "description": "A column."}]
        data, errors = _run(json.dumps(payload))
        assert not errors[KEY]
        assert json.loads(data[KEY]) == payload

    def test_extra_properties_allowed(self):
        """additionalProperties: true — extra keys must not cause failure."""
        payload = [
            {
                "field": "col_a",
                "label": "Col A",
                "description": "Desc.",
                "hxl_tag": "#indicator+value",
                "unit": "USD",
            }
        ]
        data, errors = _run(payload)
        assert not errors[KEY]

    def test_extra_properties_preserved_in_output(self):
        """Extra keys must survive the round-trip and appear in the stored JSON string."""
        payload = [
            {
                "field": "col_a",
                "label": "Col A",
                "description": "Desc.",
                "hxl_tag": "#indicator+value",
                "unit": "USD",
            }
        ]
        data, errors = _run(payload)
        assert not errors[KEY]
        stored = json.loads(data[KEY])
        assert stored[0]["hxl_tag"] == "#indicator+value"
        assert stored[0]["unit"] == "USD"

    def test_field_starts_with_underscore(self):
        """Any non-empty string is valid — underscores are fine."""
        payload = [{"field": "_private", "label": "Private", "description": "Hidden."}]
        data, errors = _run(payload)
        assert not errors[KEY]

    def test_field_with_spaces_allowed(self):
        """No pattern constraint — spaces in field names are accepted."""
        payload = [{"field": "my col", "label": "My Col", "description": "D."}]
        data, errors = _run(payload)
        assert not errors[KEY]

    def test_field_with_leading_digit_allowed(self):
        """No pattern constraint — leading digits are accepted."""
        payload = [{"field": "1col", "label": "L", "description": "D."}]
        data, errors = _run(payload)
        assert not errors[KEY]

    def test_field_long_name_allowed(self):
        """No maxLength constraint — names longer than 63 chars are accepted."""
        long_field = "a" * 100
        payload = [{"field": long_field, "label": "L", "description": "D."}]
        data, errors = _run(payload)
        assert not errors[KEY]

    def test_none_or_empty_value_is_skipped(self):
        """None/missing value means the field was not supplied — validator is a no-op."""
        data = {KEY: None}
        errors = defaultdict(list)
        hdx_validate_data_dictionary(KEY, data, errors, context={})
        assert not errors[KEY]


# ---------------------------------------------------------------------------
# Invalid inputs — JSON parsing
# ---------------------------------------------------------------------------


class TestHdxValidateDataDictionaryInvalidJson:
    def test_invalid_json_string(self):
        """Non-JSON string must produce an error."""
        data = {KEY: "not json {"}
        errors = defaultdict(list)
        with pytest.raises(StopOnError):
            hdx_validate_data_dictionary(KEY, data, errors, context={})
        assert any("valid JSON array" in msg for msg in errors[KEY])

    def test_non_array_type(self):
        """A plain dict (not a list) must produce an error."""
        data = {KEY: {"field": "x", "label": "X", "description": "D"}}
        errors = defaultdict(list)
        with pytest.raises(StopOnError):
            hdx_validate_data_dictionary(KEY, data, errors, context={})
        assert errors[KEY]

    def test_non_array_scalar(self):
        """A bare JSON string encoding a non-array scalar must produce an error."""
        data = {KEY: json.dumps(42)}
        errors = defaultdict(list)
        with pytest.raises(StopOnError):
            hdx_validate_data_dictionary(KEY, data, errors, context={})
        assert errors[KEY]


# ---------------------------------------------------------------------------
# Invalid inputs — schema violations
# ---------------------------------------------------------------------------


class TestHdxValidateDataDictionarySchemaErrors:
    def _assert_schema_error(self, value):
        data = {KEY: value}
        errors = defaultdict(list)
        with pytest.raises(StopOnError):
            hdx_validate_data_dictionary(KEY, data, errors, context={})
        assert errors[KEY], "Expected at least one schema error"
        return errors[KEY]

    def test_empty_array_rejected(self):
        """minItems: 1 — an empty list must fail."""
        self._assert_schema_error([])

    def test_missing_field_property(self):
        """Omitting 'field' must fail."""
        self._assert_schema_error([{"label": "L", "description": "D"}])

    def test_missing_label_property(self):
        """Omitting 'label' must fail."""
        self._assert_schema_error([{"field": "col", "description": "D"}])

    def test_missing_description_property(self):
        """Omitting 'description' must fail."""
        self._assert_schema_error([{"field": "col", "label": "L"}])

    def test_empty_field_string(self):
        """Empty string for 'field' must fail (minLength: 1)."""
        self._assert_schema_error([{"field": "", "label": "L", "description": "D"}])

    def test_empty_label_string(self):
        """Empty string for 'label' must fail (minLength: 1)."""
        self._assert_schema_error([{"field": "col", "label": "", "description": "D"}])

    def test_empty_description_string(self):
        """Empty string for 'description' must fail (minLength: 1)."""
        self._assert_schema_error([{"field": "col", "label": "L", "description": ""}])

    def test_item_not_an_object(self):
        """An array item that is not an object (e.g. a number) must fail."""
        self._assert_schema_error([42])

    def test_item_string_not_an_object(self):
        """An array item that is a plain string must fail."""
        self._assert_schema_error(["just a string"])

    @pytest.mark.parametrize("bad_value", [123, True, None, []])
    def test_field_wrong_type(self, bad_value):
        """Non-string values for 'field' must fail (type: string)."""
        self._assert_schema_error([{"field": bad_value, "label": "L", "description": "D"}])

    @pytest.mark.parametrize("bad_value", [123, True, None, []])
    def test_label_wrong_type(self, bad_value):
        """Non-string values for 'label' must fail (type: string)."""
        self._assert_schema_error([{"field": "col", "label": bad_value, "description": "D"}])

    @pytest.mark.parametrize("bad_value", [123, True, None, []])
    def test_description_wrong_type(self, bad_value):
        """Non-string values for 'description' must fail (type: string)."""
        self._assert_schema_error([{"field": "col", "label": "L", "description": bad_value}])


    def test_error_message_contains_location(self):
        """Error messages must include the JSON path of the failing item."""
        msgs = self._assert_schema_error(
            [{"field": "ok", "label": "L", "description": "D"},
             {"field": "", "label": "L", "description": "D"}]  # empty field at index 1
        )
        # Path should reference index 1 (second item)
        assert any("1" in msg for msg in msgs)

