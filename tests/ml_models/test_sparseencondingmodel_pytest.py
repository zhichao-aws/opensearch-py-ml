# SPDX-License-Identifier: Apache-2.0
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.
# Any modifications Copyright OpenSearch Contributors. See
# GitHub history for details.

import json
import os
import shutil
from zipfile import ZipFile

import pytest

from opensearch_py_ml.ml_models import SparseEncodingModel

TEST_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath("__file__")), "tests", "test_model_files"
)
TESTDATA_FILENAME = os.path.join(
    os.path.dirname(os.path.abspath("__file__")), "tests", "sample_zip.zip"
)
TESTDATA_UNZIP_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath("__file__")), "tests", "sample_zip"
)


def clean_test_folder(TEST_FOLDER):
    if os.path.exists(TEST_FOLDER):
        for files in os.listdir(TEST_FOLDER):
            sub_path = os.path.join(TEST_FOLDER, files)
            if os.path.isfile(sub_path):
                os.remove(sub_path)
            else:
                try:
                    shutil.rmtree(sub_path)
                except OSError as err:
                    print(
                        "Fail to delete files, please delete all files in "
                        + str(TEST_FOLDER)
                        + " "
                        + str(err)
                    )

        shutil.rmtree(TEST_FOLDER)


def check_value(expected, actual, delta):
    if isinstance(expected, float):
        assert abs(expected - actual) <= delta
    else:
        assert expected == actual


def compare_model_config(
    model_config_path,
    model_id,
    model_format,
    expected_model_description=None,
    function_name="SPARSE_ENCODING",
):
    try:
        with open(model_config_path) as json_file:
            model_config_data = json.load(json_file)
    except Exception as exec:
        assert (
            False
        ), f"Creating model config file for tracing in {model_format} raised an exception {exec}"

    assert (
        "name" in model_config_data and model_config_data["name"] == model_id
    ), f"Missing or Wrong model name in {model_format} model config file"

    assert (
        "model_format" in model_config_data
        and model_config_data["model_format"] == model_format
    ), f"Missing or Wrong model_format in {model_format} model config file"

    assert (
        "function_name" in model_config_data
        and model_config_data["function_name"] == function_name
    ), f"Missing or Wrong function_name in {model_format} model config file"

    if expected_model_description is not None:
        assert (
            "description" in model_config_data
            and model_config_data["description"] == expected_model_description
        ), f"Missing or Wrong model description in {model_format} model config file'"
    assert (
        "model_content_size_in_bytes" in model_config_data
    ), f"Missing 'model_content_size_in_bytes' in {model_format} model config file"

    assert (
        "model_content_hash_value" in model_config_data
    ), f"Missing 'model_content_hash_value' in {model_format} model config file"


def compare_model_zip_file(zip_file_path, expected_filenames, model_format):
    with ZipFile(zip_file_path, "r") as f:
        filenames = set(f.namelist())
        assert (
            filenames == expected_filenames
        ), f"The content in the {model_format} model zip file does not match the expected content: {filenames} != {expected_filenames}"


clean_test_folder(TEST_FOLDER)
# test model with a default model id opensearch-project/opensearch-neural-sparse-encoding-v1
test_model = SparseEncodingModel(folder_path=TEST_FOLDER)


def test_check_attribute():
    try:
        check_attribute = getattr(test_model, "model_id", "folder_path")
    except AttributeError:
        check_attribute = False
    assert check_attribute

    assert test_model.folder_path == TEST_FOLDER
    assert (
        test_model.model_id == "opensearch-project/opensearch-neural-sparse-encoding-v1"
    )

    default_folder = os.path.join(os.getcwd(), "opensearch_neural_sparse_model_files")

    clean_test_folder(default_folder)
    test_model0 = SparseEncodingModel()
    assert test_model0.folder_path == default_folder
    clean_test_folder(default_folder)

    clean_test_folder(TEST_FOLDER)
    test_model1 = SparseEncodingModel(
        folder_path=TEST_FOLDER, model_id="sentence-transformers/all-MiniLM-L6-v2"
    )
    assert test_model1.model_id == "sentence-transformers/all-MiniLM-L6-v2"


def test_folder_path():
    with pytest.raises(Exception) as exc_info:
        test_non_empty_path = os.path.join(
            os.path.dirname(os.path.abspath("__file__")), "tests"
        )
        SparseEncodingModel(folder_path=test_non_empty_path, overwrite=False)
    assert exc_info.type is Exception
    assert "The default folder path already exists" in exc_info.value.args[0]


def test_check_required_fields():
    # test without required_fields should raise TypeError
    with pytest.raises(TypeError):
        test_model.process_sparse_encoding()
    with pytest.raises(TypeError):
        test_model.save_as_pt()


def test_save_as_pt():
    try:
        test_model.save_as_pt(sentences=["today is sunny"])
    except Exception as exec:
        assert False, f"Tracing model in torchScript raised an exception {exec}"


def test_make_model_config_json_for_torch_script():
    model_format = "TORCH_SCRIPT"
    expected_model_description = (
        "This is a sparse encoding model for opensearch-neural-sparse-encoding-v1."
    )
    model_id = "opensearch-project/opensearch-neural-sparse-encoding-v1"
    clean_test_folder(TEST_FOLDER)
    test_model3 = SparseEncodingModel(folder_path=TEST_FOLDER)
    test_model3.save_as_pt(model_id=model_id, sentences=["today is sunny"])
    model_config_path_torch = test_model3.make_model_config_json(
        model_format="TORCH_SCRIPT", description=expected_model_description
    )

    compare_model_config(
        model_config_path_torch,
        model_id,
        model_format,
        expected_model_description=expected_model_description,
    )

    clean_test_folder(TEST_FOLDER)


def test_overwrite_description():
    model_id = "sentence-transformers/msmarco-distilbert-base-tas-b"
    model_format = "TORCH_SCRIPT"
    expected_model_description = "Expected Description"

    clean_test_folder(TEST_FOLDER)
    test_model4 = SparseEncodingModel(
        folder_path=TEST_FOLDER,
        model_id=model_id,
    )

    test_model4.save_as_pt(model_id=model_id, sentences=["today is sunny"])
    model_config_path_torch = test_model4.make_model_config_json(
        model_format=model_format, description=expected_model_description
    )
    try:
        with open(model_config_path_torch) as json_file:
            model_config_data_torch = json.load(json_file)
    except Exception as exec:
        assert (
            False
        ), f"Creating model config file for tracing in {model_format} raised an exception {exec}"

    assert (
        "description" in model_config_data_torch
        and model_config_data_torch["description"] == expected_model_description
    ), "Cannot overwrite description in model config file"

    clean_test_folder(TEST_FOLDER)


def test_long_description():
    model_id = "opensearch-project/opensearch-neural-sparse-encoding-v1"
    model_format = "TORCH_SCRIPT"
    expected_model_description = (
        "This is a sparce encoding model: It generate lots of tokens with different weight "
        "which used to semantic search."
        " The model was specifically trained for the task of semantic search."
    )

    clean_test_folder(TEST_FOLDER)
    test_model5 = SparseEncodingModel(
        folder_path=TEST_FOLDER,
        model_id=model_id,
    )

    test_model5.save_as_pt(model_id=model_id, sentences=["today is sunny"])
    model_config_path_torch = test_model5.make_model_config_json(
        model_format=model_format, description=expected_model_description
    )
    try:
        with open(model_config_path_torch) as json_file:
            model_config_data_torch = json.load(json_file)
    except Exception as exec:
        assert (
            False
        ), f"Creating model config file for tracing in {model_format} raised an exception {exec}"

    assert (
        "description" in model_config_data_torch
        and model_config_data_torch["description"] == expected_model_description
    ), "Missing or Wrong model description in model config file when the description is longer than normally."

    clean_test_folder(TEST_FOLDER)


def test_save_as_pt_with_license():
    model_id = "opensearch-project/opensearch-neural-sparse-encoding-v1"
    model_format = "TORCH_SCRIPT"
    torch_script_zip_file_path = os.path.join(
        TEST_FOLDER, "opensearch-neural-sparse-encoding-v1.zip"
    )
    torch_script_expected_filenames = {
        "opensearch-neural-sparse-encoding-v1.pt",
        "tokenizer.json",
        "LICENSE",
    }

    clean_test_folder(TEST_FOLDER)
    test_model6 = SparseEncodingModel(
        folder_path=TEST_FOLDER,
        model_id=model_id,
    )

    test_model6.save_as_pt(
        model_id=model_id, sentences=["today is sunny"], add_apache_license=True
    )

    compare_model_zip_file(
        torch_script_zip_file_path, torch_script_expected_filenames, model_format
    )

    clean_test_folder(TEST_FOLDER)


def test_default_description():
    model_id = "opensearch-project/opensearch-neural-sparse-encoding-doc-v3-distill"
    model_format = "TORCH_SCRIPT"
    expected_model_description = "This is a neural sparse encoding model: It transfers text into sparse vector, and then extract nonzero index and value to entry and weights. It serves only in ingestion and customer should use tokenizer model in query."

    clean_test_folder(TEST_FOLDER)
    test_model7 = SparseEncodingModel(
        folder_path=TEST_FOLDER,
        model_id=model_id,
    )

    test_model7.save_as_pt(model_id=model_id, sentences=["today is sunny"])
    model_config_path_torch = test_model7.make_model_config_json(
        model_format=model_format
    )
    try:
        with open(model_config_path_torch) as json_file:
            model_config_data_torch = json.load(json_file)
    except Exception as exec:
        assert (
            False
        ), f"Creating model config file for tracing in {model_format} raised an exception {exec}"

    assert (
        "description" in model_config_data_torch
        and model_config_data_torch["description"] == expected_model_description
    ), "Missing or Wrong model description in model config file when the description is not given."

    clean_test_folder(TEST_FOLDER)


def test_process_sparse_encoding():
    model_id = "opensearch-project/opensearch-neural-sparse-encoding-doc-v3-distill"

    test_model8 = SparseEncodingModel(
        folder_path=TEST_FOLDER,
        model_id=model_id,
    )

    encoding_result = test_model8.process_sparse_encoding(["hello world", "hello"])
    assert len(encoding_result[0]) == 73
    check_value(1.3667216300964355, encoding_result[0]["hello"], 0.001)
    assert len(encoding_result[1]) == 46
    check_value(1.4557286500930786, encoding_result[1]["hello"], 0.001)

    test_model8 = SparseEncodingModel(
        folder_path=TEST_FOLDER,
        model_id=model_id,
        sparse_prune_ratio=0.1,
        activation="l0",
    )
    encoding_result = test_model8.process_sparse_encoding(["hello world", "hello"])
    assert len(encoding_result[0]) == 33
    check_value(0.8615057468414307, encoding_result[0]["hello"], 0.001)
    assert len(encoding_result[1]) == 30
    check_value(0.8984234929084778, encoding_result[1]["hello"], 0.001)


clean_test_folder(TEST_FOLDER)
clean_test_folder(TESTDATA_UNZIP_FOLDER)
