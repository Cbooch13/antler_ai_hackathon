from fastapi.testclient import TestClient

from app.main import create_app
from app.services.listings import rank_listings, search_lots
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
