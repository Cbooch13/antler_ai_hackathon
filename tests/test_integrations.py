import httpx

from integrations import (
    ArcGisFeatureLayerClient,
    ArcGisFeatureLayerConfig,
    SocrataConfig,
    SocrataPermitClient,
)


def test_socrata_client_normalizes_recent_permits_and_uses_app_token() -> None:
    captured_headers = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_headers.update(request.headers)
        assert request.url.params["$limit"] == "2"
        assert "$order" not in request.url.params
        return httpx.Response(
            200,
            json=[
                {
                    "permit_number": "BP-2024-001",
                    "permit_type": "Building Permit",
                    "work_class": "New",
                    "status": "Issued",
                    "issueddate": "2024-01-15T00:00:00.000",
                    "originaladdress1": "100 Congress Ave",
                    "total_sq_ft": "2400",
                    "total_valuation": "650000",
                    "number_of_units": "2",
                    "latitude": "30.2672",
                    "longitude": "-97.7431",
                }
            ],
        )

    client = SocrataPermitClient(
        SocrataConfig(
            base_url="https://data.austintexas.gov/resource",
            dataset_id="3syk-w9eu",
            app_token="token-123",
        ),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    records = client.recent_permits(limit=2)

    assert captured_headers["x-app-token"] == "token-123"
    assert records[0].permit_id == "BP-2024-001"
    assert records[0].square_feet == 2400
    assert records[0].valuation_usd == 650000
    assert records[0].sources[0].confidence.value == "high"


def test_arcgis_client_normalizes_feature_records() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/FeatureServer/0/query")
        assert request.url.params["returnGeometry"] == "false"
        return httpx.Response(
            200,
            json={
                "features": [
                    {
                        "attributes": {
                            "OBJECTID": 42,
                            "ZONING_ZTY": "SF-3",
                            "CASE_NUM": "C14-0000",
                        }
                    }
                ]
            },
        )

    client = ArcGisFeatureLayerClient(
        ArcGisFeatureLayerConfig(
            layer_url="https://services.arcgis.com/example/arcgis/rest/services/Zoning/FeatureServer/0",
            layer_name="zoning",
        ),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    records = client.query(limit=1)

    assert records[0].feature_id == "42"
    assert records[0].layer_name == "zoning"
    assert records[0].attributes["ZONING_ZTY"] == "SF-3"
    assert records[0].sources[0].source_name == "Austin ArcGIS zoning"
