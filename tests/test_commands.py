"""Command-parser tests: transcript -> ordered text/key action plan."""

from src.commands import parse


def test_plain_text_has_no_commands():
    assert parse("just some words") == [("text", "just some words")]


def test_new_line_between_text():
    assert parse("intro new line body") == [
        ("text", "intro"),
        ("key", "enter"),
        ("text", "body"),
    ]


def test_next_line_is_an_alias_for_enter():
    assert parse("a next line b") == [
        ("text", "a"),
        ("key", "enter"),
        ("text", "b"),
    ]


def test_new_paragraph_presses_enter_twice():
    assert parse("one new paragraph two") == [
        ("text", "one"),
        ("key", "enter"),
        ("key", "enter"),
        ("text", "two"),
    ]


def test_tab_command():
    assert parse("name tab value") == [
        ("text", "name"),
        ("key", "tab"),
        ("text", "value"),
    ]


def test_command_is_case_insensitive_and_eats_whisper_punctuation():
    assert parse("Intro. New line, body") == [
        ("text", "Intro"),
        ("key", "enter"),
        ("text", "body"),
    ]


def test_tab_inside_a_word_is_not_a_command():
    assert parse("set the table") == [("text", "set the table")]


def test_command_only_transcript():
    assert parse("new line") == [("key", "enter")]


def test_german_new_line():
    assert parse("Einleitung neue Zeile Text") == [
        ("text", "Einleitung"),
        ("key", "enter"),
        ("text", "Text"),
    ]


def test_german_next_line_alias():
    assert parse("a nächste Zeile b") == [
        ("text", "a"),
        ("key", "enter"),
        ("text", "b"),
    ]


def test_german_new_paragraph_presses_enter_twice():
    assert parse("eins neuer Absatz zwei") == [
        ("text", "eins"),
        ("key", "enter"),
        ("key", "enter"),
        ("text", "zwei"),
    ]


def test_german_adjective_ending_may_vary():
    assert parse("eins neuen Absatz zwei") == [
        ("text", "eins"),
        ("key", "enter"),
        ("key", "enter"),
        ("text", "zwei"),
    ]


def test_german_tab_command():
    assert parse("Name Tabulator Wert") == [
        ("text", "Name"),
        ("key", "tab"),
        ("text", "Wert"),
    ]


def test_german_command_eats_asr_punctuation():
    assert parse("Einleitung. Neue Zeile, Text") == [
        ("text", "Einleitung"),
        ("key", "enter"),
        ("text", "Text"),
    ]


def test_zeile_inside_a_word_is_not_a_command():
    assert parse("die Zeilenumbrüche sind da") == [
        ("text", "die Zeilenumbrüche sind da")
    ]
