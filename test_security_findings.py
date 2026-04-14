from valyu.types.deepresearch import DeliverableResult


def test_valyu_py_s3_key_exposure():
    """Test that DeliverableResult does not expose internal S3 key paths."""
    assert (
        "s3_key" not in DeliverableResult.model_fields
    ), "s3_key exposes internal S3 storage architecture to SDK consumers"
