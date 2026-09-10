from travel_data import search_stays_by_city


def test_search_stays_by_city_joins_trip_and_hotel_information() -> None:
    stays = search_stays_by_city(" Boston ")

    assert len(stays) == 4
    assert stays[0]["hotel_name"] == "Harbor Lantern Hotel"
    assert stays[0]["nights"] == 2
    assert stays[0]["stay_price_usd"] == 300.0


def test_search_stays_by_city_returns_no_stays_for_an_unknown_city() -> None:
    assert search_stays_by_city("Miami") == []
