"""Test harness for running a pipeline of map reduce programs."""
import re
import pathlib
import shutil
import heapq
import contextlib
import madoop


class Pipeline:
    """Execute a pipeline of MapReduce jobs.

    Rotate working directories between jobs: job0, job1, etc.

    Optionally execute in a temporary directory.
    """

    def __init__(self, input_dir, output_dir, caplog):
        # pylint: disable=too-many-arguments
        """Create and execute MapReduce pipeline."""
        self.job_index = 0
        self.output_dir = pathlib.Path(output_dir)

        self.caplog = caplog

        # Get map and reduce executables
        self.mapper_exes, self.reducer_exes, \
            self.partitioner_exe = self.get_exes()
        assert len(self.mapper_exes) == len(self.reducer_exes)
        assert self.partitioner_exe

        # Clean up.  Remove output directory and any job-* directories.
        if self.get_job_output_dir().exists():
            shutil.rmtree(self.get_job_output_dir())
        for jobdir in self.output_dir.parent.glob("job-*"):
            shutil.rmtree(jobdir)

        # Create first job dir and copy input
        self.create_jobdir()
        shutil.copytree(input_dir,
                        self.get_job_input_dir(),
                        dirs_exist_ok=True)

        # Run pipeline
        self.run()

    def enforce_map_keyspace(self, log_text):
        """Require >1 unique intermediate key, parsed from Madoop logs.

        Looks for DEBUG lines like: "mapper-output all_unique_keys=N".
        If present, asserts N > 1 for all non-initial jobs (job1+).
        """
        pattern = re.compile(r"\bmapper-output\s+all_unique_keys=(\d+)\b")
        matches = list(pattern.finditer(log_text))

        # There should be exactly one line per job
        assert len(matches) == 1, (
            f"Internal error: expected 1 'mapper-output all_unique_keys=' "
            f"line for job {self.job_index}, found {len(matches)}."
        )

        n = int(matches[0].group(1))
        if n is not None:
            assert n > 1, (
                f"Keyspace enforcement failed: Job {self.job_index} has only "
                f"{n} unique intermediate key(s). Every stage after the "
                "document-count stage (job0) must emit multiple keys to "
                "ensure parallelizable output."
            )

    def enforce_reduce_keyspace(self):
        """Require >1 unique key in reducer outputs (part-* files).

        Scans current job's output/part-* and asserts that the set of keys
        across reducers has size > 1 (early-exits once proven).
        """
        unique_keys = set()
        for path in sorted(self.get_job_output_dir().glob("part-*")):
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    key, _, _ = line.partition("\t")
                    key = key.strip()
                    if key:
                        unique_keys.add(key)
                        if len(unique_keys) > 1:
                            break
            if len(unique_keys) > 1:
                break

        assert len(unique_keys) > 1, (
            f"Keyspace enforcement failed: Job {self.job_index} produced "
            f"only {len(unique_keys)} unique key(s) in reduce output. Every "
            "stage after document-count (job0) should emit > 1 unique key on "
            "non-trivial inputs."
        )

    def run(self):
        """Execute each job, in order."""
        use_partitioner = False
        while True:
            if use_partitioner:
                madoop.mapreduce(
                    input_path=self.get_job_input_dir(),
                    output_dir=self.get_job_output_dir(),
                    map_exe=self.get_job_mapper_exe().resolve(),
                    reduce_exe=self.get_job_reducer_exe().resolve(),
                    num_reducers=4,
                    partitioner=self.partitioner_exe.resolve(),
                )
            else:
                madoop.mapreduce(
                    input_path=self.get_job_input_dir(),
                    output_dir=self.get_job_output_dir(),
                    map_exe=self.get_job_mapper_exe().resolve(),
                    reduce_exe=self.get_job_reducer_exe().resolve(),
                    num_reducers=4,
                    partitioner=None,
                )

            # Enforce parallelization.  Each mapper and reducer should produce
            # more than one unique key.  Job 0 is an exception because it does
            # document count.
            #
            # Clear the logs in between jobs so that the logs contain only the
            # most recent stage.
            if self.job_index > 0:
                self.enforce_map_keyspace(self.caplog.text)
                self.enforce_reduce_keyspace()
            self.caplog.clear()

            # If we're about to run the last job, set flag to use
            # the custom partitioner
            if self.job_index == self.get_job_total() - 2:
                use_partitioner = True

            # Create job dir for next job, unless we're at the end
            # or we've reached the custom maximum number of jobs
            if self.job_index == 0:
                self.first_job()
            elif self.job_index < self.get_job_total() - 1:
                self.next_job()
            else:
                self.last_job()
                break

    @staticmethod
    def get_exes(mapreduce_dir=pathlib.Path()):
        """Return two lists: mapper exes and reducer exes, and custom partit.

        Valid filenames are map0.py ... map9.py, reduce0.py ... reduce9.py,
        and partition.py.

        """
        mapreduce_dir = pathlib.Path(mapreduce_dir)
        mapper_exes = []
        reducer_exes = []
        partition_exe = None
        for filename in mapreduce_dir.glob("*"):
            if re.match(r".*map[0-9]\.py$", str(filename)) is not None:
                mapper_exes.append(filename)
            elif re.match(r".*reduce[0-9]\.py$", str(filename)) is not None:
                reducer_exes.append(filename)
            elif "partition.py" in str(filename):
                partition_exe = filename
        assert mapper_exes
        assert reducer_exes
        assert partition_exe
        assert len(mapper_exes) == len(reducer_exes)
        return sorted(mapper_exes), sorted(reducer_exes), partition_exe

    def get_job_total(self):
        """Return total number of jobs."""
        assert self.mapper_exes
        assert self.reducer_exes
        assert len(self.mapper_exes) == len(self.reducer_exes)
        return len(self.mapper_exes)

    def get_job_mapper_exe(self):
        """Return the mapper executable for the current job."""
        return self.mapper_exes[self.job_index]

    def get_job_reducer_exe(self):
        """Return the reducer executable for the current job."""
        return self.reducer_exes[self.job_index]

    def create_jobdir(self):
        """Initialize directory structure."""
        assert not self.get_jobdir().exists()
        self.get_jobdir().mkdir(parents=True)
        self.get_job_input_dir().mkdir(parents=True)

    def get_jobdir(self):
        """Return a job directory name, e.g., job0, job1, etc.

        The job directory is a sibling of the output directory.
        """
        assert self.job_index <= 10
        return self.output_dir.parent/f"job-{self.job_index}"

    def get_job_input_dir(self):
        """Return the path to current input directory."""
        return self.get_jobdir()/"input"

    def get_job_output_dir(self):
        """Return the path to current output directory."""
        return self.get_jobdir()/"output"

    def get_job_output_filenames(self):
        """Return a list of output filenames."""
        return self.get_job_output_dir().glob("part-*")

    def first_job(self):
        """Advance job, copy total doc count, and update next input."""
        # copy output to total_document_count.txt
        total_doc_path = self.output_dir.parent/"total_document_count.txt"
        assert not total_doc_path.exists()
        assert (self.get_job_output_dir()/"part-00000").exists()
        shutil.copy(self.get_job_output_dir()/"part-00000", total_doc_path)

        # Save previous input directory
        prev_input_dir = self.get_job_input_dir()

        # Move to the next job and create the directories
        self.job_index += 1
        assert not self.get_jobdir().exists()
        self.create_jobdir()

        # copy input files to input of current job
        shutil.copytree(prev_input_dir,
                        self.get_job_input_dir(),
                        dirs_exist_ok=True)

    def next_job(self):
        """Advance to the next job and copy output to input."""
        # Save previous output directory
        prev_output_dir = self.get_job_output_dir()

        # Move to the next job and create the directories
        self.job_index += 1
        assert not self.get_jobdir().exists()
        self.create_jobdir()

        # Copy output files from previous job to input of current job
        for filename in prev_output_dir.glob("part-*"):
            shutil.copy(filename, self.get_job_input_dir())

    def get_output(self):
        """Return a list of output filenames."""
        return [f.resolve() for f in self.get_job_output_filenames()]

    def get_output_dir(self):
        """Return output directory."""
        return self.get_job_output_dir().resolve()

    def get_output_concat(self):
        """Concatenated output/part-* output files and return filename."""
        basename = self.get_job_output_dir().name + ".txt"
        concat_filename = self.get_jobdir()/basename

        # Merge output because segments are sorted
        with contextlib.ExitStack() as stack, \
             concat_filename.open("w") as outfile:
            infiles = [
                stack.enter_context(filename.open())
                for filename in self.get_job_output_filenames()
            ]

            for line in heapq.merge(*infiles):
                outfile.write(line)

        return concat_filename.resolve()

    def last_job(self):
        """Copy the current jobdir output to final output directory."""
        self.output_dir.mkdir(parents=True)
        for filename in self.get_job_output_filenames():
            shutil.copy(filename, self.output_dir)
