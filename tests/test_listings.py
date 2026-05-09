from fastapi.testclient import TestClient

from app.main import create_app
from app.services.listings import get_listing_detail, rank_listings, search_lots
from integrations import load_kaggle_static_listing_fixtures
from realestate_schemas import ListingSourceMode, LotSearchRequest, PropertyType, UserBuildSpec


def _adu_spec() -> UserBuildSpec:
    return UserBuildSpec(
        project_name="ADU lot search",
        property_type=PropertyType.ADU,
        total_budget_usd=850_000,
        target_lot_sqft=6_500,
        target_building_sqft=2_200,
        bedrooms=4,
        bathrooms=3,
        units=2,
        risk_tolerance="medium",
    )


def test_static_kaggle_fixtures_are_never_current_inventory() -> None:
    listings = load_kaggle_static_listing_fixtures()

    assert listings
    assert all(not listing.current_inventory for listing in listings)
    assert all(listing.source_mode == ListingSourceMode.PROTOTYPE_STATIC_DATASET for listing in listings)
    assert all("not an active listing" in (listing.prototype_note or "") for listing in listings)


def test_rank_listings_prioritizes_budget_and_spec_fit() -> None:
    ranked = rank_listings(load_kaggle_static_listing_fixtures(), _adu_spec())

    assert ranked[0].listing.listing_id == "kaggle-austin-001"
    assert ranked[0].score > ranked[-1].score
    assert "Static comp only, not active inventory." in ranked[0].warnings


def test_search_lots_rejects_unimplemented_live_sources() -> None:
    response = search_lots(
        LotSearchRequest(
            spec=_adu_spec(),
            source_mode=ListingSourceMode.LICENSED,
            limit=5,
        )
    )

    assert response.candidates == []
    assert response.current_inventory is True
    assert "Licensed MLS/IDX remains the production path." in response.warnings


def test_listing_search_route_returns_ranked_static_candidates() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/listings/search",
        json={
            "spec": _adu_spec().model_dump(by_alias=True),
            "sourceMode": "prototype_static_dataset",
            "limit": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sourceMode"] == "prototype_static_dataset"
    assert payload["currentInventory"] is False
    assert len(payload["candidates"]) == 3
    assert payload["candidates"][0]["listing"]["currentInventory"] is False
    assert payload["source"]["sourceUrl"].endswith("/ericpierce/austinhousingprices")
    assert "prototype comp" not in payload["candidates"][0]["listing"]["address"]
    assert payload["candidates"][0]["listing"]["neighborhood"] == "Hyde Park / Central Austin"


def test_listing_detail_exposes_map_context_and_missing_join_warnings() -> None:
    detail = get_listing_detail("kaggle-austin-001")

    assert detail is not None
    assert detail.parcel is not None
    assert detail.map_context.latitude == 30.298
    assert detail.map_context.street_view_url is not None
    assert "4307+Avenue+G" in detail.map_context.street_view_url
    assert "viewpoint=30.298" not in detail.map_context.street_view_url
    assert "No zoning feature has been joined to this prototype row yet." in detail.warnings


def test_listing_detail_route_404s_unknown_listing() -> None:
    client = TestClient(create_app())

    response = client.get("/listings/not-real/detail")

    assert response.status_code == 404


def test_listing_detail_route_returns_context() -> None:
    client = TestClient(create_app())

    response = client.get("/listings/kaggle-austin-001/detail")

    assert response.status_code == 200
    payload = response.json()
    assert payload["listing"]["listingId"] == "kaggle-austin-001"
    assert payload["listing"]["neighborhood"] == "Hyde Park / Central Austin"
    assert payload["parcel"]["parcelId"] == "prototype-kaggle-austin-001"
    assert payload["mapContext"]["streetViewUrl"].startswith("https://www.google.com/maps/search/")
