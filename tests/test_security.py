def test_no_s3_key_in_deliverable_result_py():
    import pathlib

    f = pathlib.Path("/workspace/repos/valyu-py/valyu/types/deepresearch.py")
    content = f.read_text()
    start = content.find("DeliverableResult")
    end = (
        content.find("\nclass ", start + 1)
        if "\nclass " in content[start + 1 :]
        else len(content)
    )
    block = content[start:end]
    assert (
        "s3_key" not in block
    ), "Internal s3_key field still exposed in DeliverableResult class"
