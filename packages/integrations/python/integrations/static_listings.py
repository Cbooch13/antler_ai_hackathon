from datetime import datetime, timezone

from realestate_schemas import Confidence, Listing, ListingSourceMode, SourceMetadata

KAGGLE_AUSTIN_HOUSING_URL = "https://www.kaggle.com/datasets/ericpierce/austinhousingprices"
KAGGLE_AUSTIN_HOUSING_LICENSE = "GPL-2.0"


def kaggle_source_metadata() -> SourceMetadata:
    return SourceMetadata(
        source_name="Kaggle Austin housing prices dataset",
        source_url=KAGGLE_AUSTIN_HOUSING_URL,
        retrieved_at=datetime.now(timezone.utc),
        confidence=Confidence.LOW,
        license_name=KAGGLE_AUSTIN_HOUSING_LICENSE,
        notes=[
            "Static MVP fallback dataset, not current inventory.",
            "Use for demos, ranking tests, and workflow validation only.",
            "Cross-reference with Travis/TCAD or official records before decisions.",
        ],
    )


def load_kaggle_static_listing_fixtures() -> list[Listing]:
    source = kaggle_source_metadata()
    prototype_note = (
        "Prototype static dataset row. This is not an active listing or live MLS availability."
    )
    return [
        Listing(
            listing_id="kaggle-austin-001",
            address="4307 Avenue G, Austin, TX 78751",
            price_usd=825_000,
            lot_sqft=6_600,
            building_sqft=2_150,
            bedrooms=4,
            bathrooms=3,
            units=2,
            latitude=30.298,
            longitude=-97.741,
            source_mode=ListingSourceMode.PROTOTYPE_STATIC_DATASET,
            current_inventory=False,
            data_year=2021,
            prototype_note=prototype_note,
            sources=[source],
        ),
        Listing(
            listing_id="kaggle-austin-002",
            address="1206 Chicon St, Austin, TX 78702",
            price_usd=695_000,
            lot_sqft=5_200,
            building_sqft=1_850,
            bedrooms=3,
            bathrooms=2,
            units=1,
            latitude=30.263,
            longitude=-97.701,
            source_mode=ListingSourceMode.PROTOTYPE_STATIC_DATASET,
            current_inventory=False,
            data_year=2021,
            prototype_note=prototype_note,
            sources=[source],
        ),
        Listing(
            listing_id="kaggle-austin-003",
            address="5404 Duval St, Austin, TX 78751",
            price_usd=1_050_000,
            lot_sqft=7_400,
            building_sqft=3_050,
            bedrooms=5,
            bathrooms=4,
            units=2,
            latitude=30.319,
            longitude=-97.724,
            source_mode=ListingSourceMode.PROTOTYPE_STATIC_DATASET,
            current_inventory=False,
            data_year=2021,
            prototype_note=prototype_note,
            sources=[source],
        ),
        Listing(
            listing_id="kaggle-austin-004",
            address="2505 Wilson St, Austin, TX 78704",
            price_usd=575_000,
            lot_sqft=8_100,
            building_sqft=1_450,
            bedrooms=3,
            bathrooms=2,
            units=1,
            latitude=30.23,
            longitude=-97.775,
            source_mode=ListingSourceMode.PROTOTYPE_STATIC_DATASET,
            current_inventory=False,
            data_year=2021,
            prototype_note=prototype_note,
            sources=[source],
        ),
        Listing(
            listing_id="kaggle-austin-005",
            address="1704 Hartford Rd, Austin, TX 78703",
            price_usd=1_450_000,
            lot_sqft=10_500,
            building_sqft=3_900,
            bedrooms=5,
            bathrooms=4.5,
            units=1,
            latitude=30.302,
            longitude=-97.802,
            source_mode=ListingSourceMode.PROTOTYPE_STATIC_DATASET,
            current_inventory=False,
            data_year=2021,
            prototype_note=prototype_note,
            sources=[source],
        ),
    ]
