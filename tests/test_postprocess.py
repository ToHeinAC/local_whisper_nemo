"""Transcript cleanup tests: hesitations out, spelled-out numbers to digits."""

from src.postprocess import normalize


def test_plain_text_is_untouched():
    assert normalize("das ist ein Test", "de-DE") == "das ist ein Test"


def test_hesitations_are_removed_with_their_commas():
    assert normalize("Das ist, äh, ein Test.", "de-DE") == "Das ist ein Test."


def test_english_hesitations_are_removed():
    assert normalize("This is, uh, a test.", "en-US") == "This is a test."


def test_leading_hesitation_keeps_the_sentence_capitalised():
    assert normalize("Ähm, das war es.", "de-DE") == "Das war es."


def test_repeated_and_stretched_hesitations():
    assert normalize("Also ähm ähhh hmm ja", "de-DE") == "Also ja"


def test_hesitation_inside_a_word_is_kept():
    # "ähnlich" starts with "äh"; \b must stop the match.
    assert normalize("etwas ähnliches", "de-DE") == "etwas ähnliches"


def test_um_is_kept_because_german_needs_it():
    assert normalize("Ich gehe früher, um pünktlich zu sein.", "de-DE") == (
        "Ich gehe früher, um pünktlich zu sein."
    )


def test_german_numbers_become_digits():
    assert normalize("dreiundzwanzig Grad", "de-DE") == "23 Grad"


def test_german_ordinals_and_decimals():
    assert normalize("der dritte Versuch", "de-DE") == "der 3. Versuch"
    assert normalize("drei Komma fünf Prozent", "de-DE") == "3,5 Prozent"


def test_english_numbers_ordinals_and_decimals():
    assert normalize("twenty three degrees", "en-US") == "23 degrees"
    assert normalize("the third attempt", "en-US") == "the 3rd attempt"
    assert normalize("three point five percent", "en-US") == "3.5 percent"


def test_indefinite_article_is_not_turned_into_a_digit():
    """The reason isolated 1 is left alone: "ein" is the German article."""
    assert normalize("ein Haus und ein Auto", "de-DE") == "ein Haus und ein Auto"
    assert normalize("one house", "en-US") == "one house"


def test_auto_locale_converts_either_language():
    assert normalize("dreiundzwanzig Grad", "auto") == "23 Grad"
    assert normalize("twenty three degrees", "auto") == "23 degrees"


def test_hesitation_inside_a_number_does_not_block_conversion():
    assert normalize("drei äh und zwanzig Grad", "de-DE") == "23 Grad"


def test_transcript_that_is_only_a_hesitation_becomes_empty():
    assert normalize("Ähm.", "de-DE") == "."
