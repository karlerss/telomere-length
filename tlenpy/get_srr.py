import click
from Queue import Queue
from multiprocessing import Process
import csv
import logging
from job import Job
from functions import *

logging.basicConfig(level=logging.DEBUG)
root = logging.getLogger()
root.removeHandler(root.handlers[0])
logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)
q_download = Queue()
q_process = Queue(10)
paths = dict()


def downloader():
    while True:
        job = q_download.get()

        successful = job.fetch()

        if not successful:
            q_download.put(job)
            q_download.task_done()
        else:
            # Add to processing queue if slot available. Otherwise block.
            q_process.put(job)

            # Keep the lock until job is in process-queue.
            # Keeps process queue from joining prematurely.
            q_download.task_done()


def processor():
    logger.info('Spawned worker thread!')
    while True:
        # Block until job available.
        job = q_process.get()
        job.process()
        q_process.task_done()


@click.command()
@click.argument('run_table', type=click.File())
@click.argument('query_list', type=click.File())
@click.option('--data_root', '-d', default='/data', type=click.Path(exists=True),
              help='Directory for outputs and temp files.')
@click.option('--ncbi_root', '-n', default='/data/ncbi', type=click.Path(exists=False),
              help='The ncbi data directory. Can be configured from ~/.ncbi/user-settings.mkfg')
@click.option('--check_fasta', type=click.BOOL, default=False)
@click.option('--fasta_limit', type=click.INT, default=0,
              help='Set limit on dumped fasta lines. 3000 is optimal for debugging.')
@click.option('--processing_cores', '-p', default=1, type=click.INT)
def main(run_table, query_list, data_root, ncbi_root, check_fasta, fasta_limit, processing_cores):
    global paths

    paths = setup_tree(data_root)
    paths['ncbi'] = ncbi_root
    add_file_logger(paths, logger)

    check_bins(logger)

    Job.set_fasta_limit(fasta_limit)
    Job.set_fasta_check(check_fasta)
    Job.set_logger(logger)
    Job.set_paths(paths)
    Job.set_q_download(q_download)
    Job.set_q_process(q_process)
    Job.set_kmer_sample_path(os.path.realpath(query_list.name))

    # TODO: remove sra lock and cache files before run

    with run_table as tsv:
        reader = csv.reader(tsv, dialect="excel-tab")
        next(reader, None)  # Skip header
        for line in reader:
            name = line[8]
            q_download.put(Job(name))

    # print q_download.qsize()

    # spawn worker threads
    t_downloader = Process(target=downloader)
    t_downloader.daemon = True
    t_downloader.start()

    workers = list()
    for i in range(0, processing_cores):
        t_processor = Process(target=processor)
        t_processor.daemon = True
        t_processor.start()
        workers.append(t_processor)

    # Block until downloads empty.
    q_download.join()

    # Block until everything processed.
    q_process.join()


if __name__ == '__main__':
    main()
