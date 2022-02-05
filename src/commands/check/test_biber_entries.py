import re
import pytest

from src.util.text import OMISSION_CHAR, TranscriptionFunctions, jaccard_similarity
from src.util.BibEntry import BibEntry

from .fields_per_types import fields_per_types
from .utils import biber_entries_gen, get_entry_by_id

IGNORE_DUPLICATION_PROPERTY_NAME = "noduplication"
DUPLICATION_THRESHOLD = 0.8


@pytest.mark.parametrize("entry", biber_entries_gen(), ids=lambda entry: entry.id)
def test_characters_in_id(entry: BibEntry):
    assert re.match(rf"^[a-zA-Z0-9_{OMISSION_CHAR}]+$", entry.id) is not None, \
        "ID '%s' should contain a-z, A-Z, 0-9 or %s only" % (entry.id, OMISSION_CHAR)


@pytest.mark.parametrize("entry", biber_entries_gen(), ids=lambda entry: entry.id)
def test_readable_id(entry: BibEntry):
    clean_title = TranscriptionFunctions.lower(TranscriptionFunctions.drop_specials(entry["title"]))
    assert re.match(rf"^{clean_title}", entry.id), \
        "ID '%s' should start with an easy to read version of the title" % entry.id


@pytest.mark.parametrize("entry", biber_entries_gen(), ids=lambda entry: entry.id)
def test_entry_type(entry: BibEntry):
    assert entry.entry_type in fields_per_types


@pytest.mark.parametrize("entry", biber_entries_gen(), ids=lambda entry: entry.id)
def test_field_type(entry: BibEntry):
    for quantifier in fields_per_types.get(entry.entry_type, ()):
        quantifier.check(entry.id, entry)


@pytest.mark.parametrize("entry", biber_entries_gen(), ids=lambda entry: entry.id)
@pytest.mark.parametrize("other_entry", biber_entries_gen(), ids=lambda entry: entry.id)
def test_no_duplication(entry: BibEntry, other_entry: BibEntry):
    if entry is other_entry:
        return

    entry_ignored_keys = entry.fields.get(IGNORE_DUPLICATION_PROPERTY_NAME, '').split(',')
    if other_entry.id in entry_ignored_keys:
        return

    other_entry_ignored_keys = other_entry.fields.get(IGNORE_DUPLICATION_PROPERTY_NAME, '').split(',')
    if entry.id in other_entry_ignored_keys:
        return

    similarity = jaccard_similarity(entry["title"], other_entry["title"])

    assert similarity < DUPLICATION_THRESHOLD, \
        "Entries '%s' (line %d) and '%s' (line %d) are potentially duplicates, similarity = %.2f" \
        % (entry.id, entry.line_number, other_entry.id, other_entry.line_number, similarity)


@pytest.mark.parametrize("entry", biber_entries_gen(), ids=lambda entry: entry.id)
def test_right_use_of_noduplication(entry: BibEntry):
    ignored_keys = [k for k in entry.fields.get(IGNORE_DUPLICATION_PROPERTY_NAME, '').split(',') if k != '']
    for ignored_key in ignored_keys:
        assert get_entry_by_id(ignored_key), \
            'Unknown key "%s" specified as %s in entry "%s"' % (ignored_key, IGNORE_DUPLICATION_PROPERTY_NAME, entry.id)

        _entry = get_entry_by_id(ignored_key)
        similarity = jaccard_similarity(entry["title"], _entry["title"])

        assert similarity >= DUPLICATION_THRESHOLD, \
            'Entry "%s" and entry "%s" (specified in "%s") are not real duplicates, similarity = %.2f' \
            % (entry.id, ignored_key, entry.id, similarity)

        _ignored_keys = [k for k in _entry.fields.get(IGNORE_DUPLICATION_PROPERTY_NAME, '').split(',') if k != '']
        assert entry.id in _ignored_keys, \
            'Key "%s" is missing among "%s" references in entry "%s"' \
            % (entry.id, IGNORE_DUPLICATION_PROPERTY_NAME, ignored_key)
