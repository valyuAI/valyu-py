"""Test that DeliverableResult does not expose internal s3_key field."""


def test_valyu_py_deliverable_result_no_s3_key():
    from valyu.types.deepresearch import DeliverableResult

    assert "s3_key" not in DeliverableResult.model_fields, (
        "s3_key is an internal AWS S3 storage path and must not be exposed in the public SDK type"
    )
