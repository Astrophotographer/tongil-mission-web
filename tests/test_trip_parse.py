from api._trip_parse import parse_primary_json, strip_code_fence


def test_strip_fence():
    raw = "```json\n{\"recommended_site\":\"임진각\"}\n```"
    assert "임진각" in strip_code_fence(raw)


def test_parse_primary_minimal():
    data = parse_primary_json(
        '{"recommended_site":"임진각","nearby_area":"파주 임진각","reason":"r","learning_goals":["g"],"field_missions":["m"]}'
    )
    assert data["recommended_site"] == "임진각"
