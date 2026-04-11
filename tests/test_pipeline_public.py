"""Public Inverted Index MapReduce pipeline tests."""

from pathlib import Path
import logging
import shutil
import madoop
import utils
from utils import TESTDATA_DIR


def test_doc_count_one_mapper(tmpdir, caplog):
    """Doc count MapReduce job with one input, resulting in one map task.

    Note: 'tmpdir' is a fixture provided by the pytest package.  It creates a
    unique temporary directory before the test runs, and removes it afterward.
    https://docs.pytest.org/en/6.2.x/tmpdir.html#the-tmpdir-fixture
    """
    shutil.copy("inverted_index/map0.py", tmpdir)
    shutil.copy("inverted_index/reduce0.py", tmpdir)

    # Run MapReduce job
    with tmpdir.as_cwd(), caplog.at_level(logging.DEBUG, logger="madoop"):
        madoop.mapreduce(
            input_path=TESTDATA_DIR/"test_doc_count_one_mapper/crawl",
            output_dir=tmpdir/"output",
            map_exe="./map0.py",
            reduce_exe="./reduce0.py",
            num_reducers=4,
            partitioner=None,
        )

    # Verify doc count
    doc_count_path = tmpdir/"output/part-00000"
    doc_count_str = Path(doc_count_path).read_text(encoding='utf-8')
    doc_count = int(doc_count_str)
    assert doc_count == 3


def test_num_phases():
    """There should be more than one MapReduce program in the pipeline."""
    mapper_exes, reducer_exes, partitioner_exe = utils.Pipeline.get_exes(
        "inverted_index/"
    )
    num_mappers = len(mapper_exes)
    num_reducers = len(reducer_exes)
    assert num_mappers > 1, "Must use more than 1 map phase"
    assert num_reducers > 1, "Must use more than 1 reduce phase"
    assert partitioner_exe, "Did you forget to create partition.py?"


def test_simple(tmpdir, caplog):
    """Simple input with no stopwords, no uppercase and no alphanumerics.

    A basic document with no stopwords, upppercase letters, numbers,
    non-alphanumeric characters, or repeated words.

    Note: 'tmpdir' is a fixture provided by the pytest package.  It creates a
    unique temporary directory before the test runs, and removes it afterward.
    https://docs.pytest.org/en/6.2.x/tmpdir.html#the-tmpdir-fixture
    """
    utils.copyglob("inverted_index/map?.py", tmpdir)
    utils.copyglob("inverted_index/reduce?.py", tmpdir)
    utils.copyglob("inverted_index/partition.py", tmpdir)
    utils.copyglob("inverted_index/stopwords.txt", tmpdir)

    # Start pipeline mapreduce job
    with tmpdir.as_cwd(), caplog.at_level(logging.DEBUG, logger="madoop"):
        pipeline = utils.Pipeline(
            input_dir=TESTDATA_DIR/"test_pipeline03/crawl",
            output_dir=tmpdir/"output",
            caplog=caplog
        )

        # Concatenate output files to output.txt
        output_filename = pipeline.get_output_concat()

    # Verify output
    utils.assert_inverted_index_eq(
        output_filename,
        TESTDATA_DIR/"test_pipeline03/expected.txt",
    )


def test_example(tmpdir, caplog):
    """Same as the input as the one given in example_crawl.

    This test tests the example_crawl given to the students
    and compares it with example_output.

    Note: 'tmpdir' is a fixture provided by the pytest package. It creates a
    unique temporary directory before the test runs, and removes it afterward.
    https://docs.pytest.org/en/6.2.x/tmpdir.html#the-tmpdir-fixture
    """
    utils.copyglob("inverted_index/map?.py", tmpdir)
    utils.copyglob("inverted_index/reduce?.py", tmpdir)
    utils.copyglob("inverted_index/partition.py", tmpdir)
    utils.copyglob("inverted_index/stopwords.txt", tmpdir)

    # Run pipeline mapreduce job
    with tmpdir.as_cwd(), caplog.at_level(logging.DEBUG, logger="madoop"):
        pipeline = utils.Pipeline(
            input_dir=TESTDATA_DIR/"test_pipeline16/crawl",
            output_dir=tmpdir/"output",
            caplog=caplog
        )
        output_dir = pipeline.get_output_dir()

    # Verify output
    utils.assert_inverted_index_eq(
        output_dir,
        TESTDATA_DIR/"test_pipeline16/expected",
    )


def test_uppercase(tmpdir, caplog):
    """Input with uppercase characters.

    This test checks if students handle upper case characters correctly,
    they should essentially be replaced with lower case characters.  There
    are no stopwords, numbers or non-alphanumeric characters present in
    this test.

    Note: 'tmpdir' is a fixture provided by the pytest package.  It creates a
    unique temporary directory before the test runs, and removes it afterward.
    https://docs.pytest.org/en/6.2.x/tmpdir.html#the-tmpdir-fixture
    """
    utils.copyglob("inverted_index/map?.py", tmpdir)
    utils.copyglob("inverted_index/reduce?.py", tmpdir)
    utils.copyglob("inverted_index/partition.py", tmpdir)
    utils.copyglob("inverted_index/stopwords.txt", tmpdir)

    # Run pipeline mapreduce job
    with tmpdir.as_cwd(), caplog.at_level(logging.DEBUG, logger="madoop"):
        pipeline = utils.Pipeline(
            input_dir=TESTDATA_DIR/"test_pipeline04/crawl",
            output_dir=tmpdir/"output",
            caplog=caplog
        )
        output_filename = pipeline.get_output_concat()

    # Verify output
    utils.assert_inverted_index_eq(
        output_filename,
        TESTDATA_DIR/"test_pipeline04/expected.txt",
    )


def test_uppercase_and_numbers(tmpdir, caplog):
    """Input with uppercase characters and numbers.

    This test checks that students are handling numbers correctly, which means
    leaving them inside the word they are a part of. This test also contains
    upper case characters. There are no stopwords or non-alphanumeric
    characters present in this test.

    Note: 'tmpdir' is a fixture provided by the pytest package.  It creates a
    unique temporary directory before the test runs, and removes it afterward.
    https://docs.pytest.org/en/6.2.x/tmpdir.html#the-tmpdir-fixture
    """
    utils.copyglob("inverted_index/map?.py", tmpdir)
    utils.copyglob("inverted_index/reduce?.py", tmpdir)
    utils.copyglob("inverted_index/partition.py", tmpdir)
    utils.copyglob("inverted_index/stopwords.txt", tmpdir)

    # Run pipeline mapreduce job
    with tmpdir.as_cwd(), caplog.at_level(logging.DEBUG, logger="madoop"):
        pipeline = utils.Pipeline(
            input_dir=TESTDATA_DIR/"test_pipeline05/crawl",
            output_dir=tmpdir/"output",
            caplog=caplog
        )
        output_filename = pipeline.get_output_concat()

    # Verify output
    utils.assert_inverted_index_eq(
        output_filename,
        TESTDATA_DIR/"test_pipeline05/expected.txt",
    )


def test_non_alphanumeric(tmpdir, caplog):
    """Input with non-alphanumeric characters.

    This test checks that students are handling non-alphanumeric characters
    properly, i.e., removing them from the word. If a token contains only
    non-alphanumeric characters then it is omitted from the inverted
    index. There are uppercase characters and numbers in this test. There are
    no stopwords.

    Note: 'tmpdir' is a fixture provided by the pytest package.  It creates a
    unique temporary directory before the test runs, and removes it afterward.
    https://docs.pytest.org/en/6.2.x/tmpdir.html#the-tmpdir-fixture
    """
    utils.copyglob("inverted_index/map?.py", tmpdir)
    utils.copyglob("inverted_index/reduce?.py", tmpdir)
    utils.copyglob("inverted_index/partition.py", tmpdir)
    utils.copyglob("inverted_index/stopwords.txt", tmpdir)

    # Run pipeline mapreduce job with 1 mapper and 1 reducer
    with tmpdir.as_cwd(), caplog.at_level(logging.DEBUG, logger="madoop"):
        pipeline = utils.Pipeline(
            input_dir=TESTDATA_DIR/"test_pipeline06/crawl",
            output_dir=tmpdir/"output",
            caplog=caplog
        )
        output_filename = pipeline.get_output_concat()

    # Verify output
    utils.assert_inverted_index_eq(
        output_filename,
        TESTDATA_DIR/"test_pipeline06/expected.txt",
    )


def test_many_docs(tmpdir, caplog):
    """Term appears in multiple documents.

    This test checks that students are properly handling the case of a term
    appearing in multiple documents. The inverted index entry should contain a
    chain of document ids.

    Note: 'tmpdir' is a fixture provided by the pytest package.  It creates a
    unique temporary directory before the test runs, and removes it afterward.
    https://docs.pytest.org/en/6.2.x/tmpdir.html#the-tmpdir-fixture
    """
    utils.copyglob("inverted_index/map?.py", tmpdir)
    utils.copyglob("inverted_index/reduce?.py", tmpdir)
    utils.copyglob("inverted_index/partition.py", tmpdir)
    utils.copyglob("inverted_index/stopwords.txt", tmpdir)

    # Run pipeline mapreduce job
    with tmpdir.as_cwd(), caplog.at_level(logging.DEBUG, logger="madoop"):
        pipeline = utils.Pipeline(
            input_dir=TESTDATA_DIR/"test_pipeline10/crawl",
            output_dir=tmpdir/"output",
            caplog=caplog
        )
        output_dir = pipeline.get_output_dir()

    # There should be two output inverted index as docids 25 and 31 will go in
    # one inverted index and docid 30 will go in another.
    utils.assert_inverted_index_eq(
        output_dir,
        TESTDATA_DIR/"test_pipeline10/expected",
    )


def test_segments(tmpdir, caplog):
    """Output is segmented by document.

    This test checks that students are properly distributing documents across
    the output inverted indexes.

    Note: 'tmpdir' is a fixture provided by the pytest package.  It creates a
    unique temporary directory before the test runs, and removes it afterward.
    https://docs.pytest.org/en/6.2.x/tmpdir.html#the-tmpdir-fixture
    """
    utils.copyglob("inverted_index/map?.py", tmpdir)
    utils.copyglob("inverted_index/reduce?.py", tmpdir)
    utils.copyglob("inverted_index/partition.py", tmpdir)
    utils.copyglob("inverted_index/stopwords.txt", tmpdir)

    # Run pipeline mapreduce job
    with tmpdir.as_cwd(), caplog.at_level(logging.DEBUG, logger="madoop"):
        pipeline = utils.Pipeline(
            input_dir=TESTDATA_DIR/"test_pipeline14/crawl",
            output_dir=tmpdir/"output",
            caplog=caplog
        )
        output_dir = pipeline.get_output_dir()

    # Verify output
    utils.assert_inverted_index_eq(
        output_dir,
        TESTDATA_DIR/"test_pipeline14/expected",
    )


def test_sample_inverted_index(tmp_path):
    """Checks a few lines of the large inverted index.

    This test checks the student's large inverted index
    made using inverted_index/crawl/
    with a few lines from the instructor solution.

    Note: 'tmp_path' is a fixture provided by the pytest package.  It creates a
    unique temporary directory before the test runs, and removes it afterward.
    https://docs.pytest.org/en/6.2.x/tmpdir.html

    """
    # Terms we're checking
    # $ grep '^FIXME_TERM ' output/part-* | cut -d' ' -f1-5
    terms = [
        "boingboing",
        "buzzwords",
        "kloofendal",
        "metrics",
        "mutexes",
        "nanoscale",
        "programming",
        "riverfront",
    ]

    # Verify inverted index file are copied to
    # ./index_server/index/inverted_index
    inverted_index_dir = Path("index_server/index/inverted_index")
    assert inverted_index_dir.is_dir()
    inverted_index_paths = inverted_index_dir.glob("inverted_index_*.txt")
    inverted_index_paths = sorted(inverted_index_paths)
    assert inverted_index_paths, \
        ("Did you forget to copy the inverted_index_*.txt files"
            f" to {inverted_index_dir}?")
    assert len(inverted_index_paths) == 3

    # Filter student inverted index files, keeping only the subset of terms
    # that we're checking
    for inpath in inverted_index_paths:
        outpath = tmp_path/inpath.name
        filter_inverted_index(inpath, outpath, terms)

    # Compare filtered student inverted index files in tmp directory to
    # instructor solution inverted index
    utils.assert_inverted_index_eq(tmp_path, TESTDATA_DIR/"test_pipeline15")


def filter_inverted_index(inpath, outpath, terms):
    """Filter inpath, writing lines in terms list to outpath."""
    with inpath.open() as infile, outpath.open("w") as outfile:
        for line in infile:
            term = line.partition(" ")[0]
            if term in terms:
                outfile.write(line)
