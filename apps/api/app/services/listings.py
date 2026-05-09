from integrations import kaggle_source_metadata, load_kaggle_static_listing_fixtures
from realestate_schemas import (
    Listing,
    ListingSourceMode,
    LotSearchRequest,
    LotSearchResponse,
    RankedListing,
    UserBuildSpec,
)


STATIC_DATASET_WARNING = (
    "Results come from a static Kaggle prototype dataset and are not active listings."
)


def search_lots(request: LotSearchRequest) -> LotSearchResponse:
    if request.source_mode != ListingSourceMode.PROTOTYPE_STATIC_DATASET:
        return LotSearchResponse(
            source_mode=request.source_mode,
            current_inventory=request.source_mode == ListingSourceMode.LICENSED,
            candidates=[],
            source=None,
            warnings=[
                "Only prototype_static_dataset listing discovery is implemented in Stage 3.",
                "Licensed MLS/IDX remains the production path.",
            ],
        )

    ranked = rank_listings(load_kaggle_static_listing_fixtures(), request.spec)
    return LotSearchResponse(
        source_mode=ListingSourceMode.PROTOTYPE_STATIC_DATASET,
        current_inventory=False,
        candidates=ranked[: request.limit],
        source=kaggle_source_metadata(),
        warnings=[
            STATIC_DATASET_WARNING,
            "Cross-reference parcel/property identity with Travis/TCAD or official records.",
        ],
    )


def rank_listings(listings: list[Listing], spec: UserBuildSpec) -> list[RankedListing]:
    ranked = [_score_listing(listing, spec) for listing in listings]
    return sorted(ranked, key=lambda candidate: candidate.score, reverse=True)


def _score_listing(listing: Listing, spec: UserBuildSpec) -> RankedListing:
    score = 100.0
    reasons: list[str] = []
    warnings: list[str] = []

    budget_delta = (listing.price_usd - spec.total_budget_usd) / spec.total_budget_usd
    if budget_delta <= 0:
        reasons.append("At or below budget.")
        score += min(8, abs(budget_delta) * 10)
    else:
        penalty = min(45, budget_delta * 100)
        score -= penalty
        warnings.append("Above target budget.")

    if spec.target_lot_sqft and listing.lot_sqft:
        ratio = listing.lot_sqft / spec.target_lot_sqft
        if ratio >= 1:
            reasons.append("Meets or exceeds target lot size.")
            score += min(8, (ratio - 1) * 10)
        else:
            score -= min(25, (1 - ratio) * 50)
            warnings.append("Below target lot size.")

    if spec.target_building_sqft and listing.building_sqft:
        ratio = listing.building_sqft / spec.target_building_sqft
        if 0.85 <= ratio <= 1.35:
            reasons.append("Comparable building size.")
            score += 6
        elif ratio < 0.85:
            score -= min(18, (0.85 - ratio) * 40)
            warnings.append("Smaller than target building size.")
        else:
            score -= min(8, (ratio - 1.35) * 12)

    if spec.bedrooms is not None and listing.bedrooms is not None:
        if listing.bedrooms >= spec.bedrooms:
            reasons.append("Meets bedroom target.")
            score += 4
        else:
            score -= (spec.bedrooms - listing.bedrooms) * 5
            warnings.append("Below bedroom target.")

    if listing.units >= spec.units:
        reasons.append("Meets unit-count target.")
        score += 5
    else:
        score -= (spec.units - listing.units) * 10
        warnings.append("Below unit-count target.")

    if not listing.current_inventory:
        warnings.append("Static comp only, not active inventory.")

    bounded = max(0, min(100, round(score, 2)))
    return RankedListing(
        listing=listing,
        score=bounded,
        rank_reasons=reasons,
        warnings=warnings,
    )
