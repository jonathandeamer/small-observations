from datetime import datetime

from ingest import slug


def test_basic_slug_from_date_and_city():
    s = slug.build(datetime(2018, 7, 14), city="Paris", existing=set())
    assert s == "2018-07-14-paris"


def test_slug_normalizes_diacritics_and_spaces():
    s = slug.build(datetime(2021, 3, 8), city="São Paulo", existing=set())
    assert s == "2021-03-08-sao-paulo"


def test_slug_appends_suffix_on_collision():
    existing = {"2018-07-14-paris"}
    s = slug.build(datetime(2018, 7, 14), city="Paris", existing=existing)
    assert s == "2018-07-14-paris-2"


def test_slug_appends_increasing_suffix():
    existing = {"2018-07-14-paris", "2018-07-14-paris-2", "2018-07-14-paris-3"}
    s = slug.build(datetime(2018, 7, 14), city="Paris", existing=existing)
    assert s == "2018-07-14-paris-4"


def test_slug_handles_missing_city():
    s = slug.build(datetime(2018, 7, 14), city=None, existing=set())
    assert s == "2018-07-14"
