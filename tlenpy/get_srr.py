import click
import os
import os.path
import shutil
from ftplib import FTP
from Queue import Queue
from threading import Thread
import csv
import time
import subprocess
import logging
from logging.handlers import TimedRotatingFileHandler

logging.basicConfig(level=logging.DEBUG)

h1 = logging.StreamHandler()
root = logging.getLogger()
root.removeHandler(root.handlers[0])

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)

logger.addHandler(handler)


def which(program):
    '''
    http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
    '''
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def setup_tree(path):
    if os.path.isabs(path):
        data_base = path
    else:
        data_base = os.path.join(os.getcwd(), path)

    if not os.path.exists(data_base):
        os.mkdir(data_base)

    directories = ['list', 'result', 'logs', 'fasta']

    paths = dict()

    for d in directories:
        if not os.path.exists(os.path.join(data_base, d)):
            os.mkdir(os.path.join(data_base, d))
        paths[d] = os.path.join(data_base, d)

    return paths


def check_bins():
    bin_names = ['prefetch', 'fastq-dump', 'glistmaker', 'glistquery']
    failed = False
    for b in bin_names:
        r = which(b)
        if not r:
            logger.error('Missing binary: "%s"', b)
            failed = True
        else:
            logger.info('Binary OK: "%s"', b)

    if failed:
        raise EnvironmentError("Missing binary.")


def add_file_logger():
    global paths
    fh = TimedRotatingFileHandler(os.path.join(paths['logs'], 'log'), when='midnight', backupCount=7)
    fh.setFormatter(formatter)
    fh.setLevel(logging.INFO)
    fh.suffix = "%Y-%m-%d"
    logger.addHandler(fh)


class Job:
    def __init__(self, name):
        self.name = name
        self.sra_downloaded = False
        self.sra_deleted = False
        self.fasta_dumped = False
        self.fasta_deleted = False
        self.list_created = False
        self.list_deleted = False
        self.result_dumped = False

    @staticmethod
    def call(command):
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            # If we don't need real time logging, we could just use p.communicate.
            out = p.stdout.readline()
            if out.rstrip('\n'):
                logger.info(out.rstrip('\n'))
            err = p.stderr.readline()
            if err.rstrip('\n'):
                logger.error(err.rstrip('\n'))
            if not err and not out:
                logger.debug("Breaking out of std capture loop!")
                break
        p.wait()
        return p.returncode

    def fetch(self):
        # Call prefetch
        res = self.call(['prefetch', self.name, '-v', '-L', '5'])
        if res is 0:
            self.sra_downloaded = True
        logger.info('Fetched %s | %d in download queue', self.name, q_download.qsize())

    def process(self):
        # Call fastq-dump.

        res = self.call(['fastq-dump', self.name, '-O', paths['fasta'], '--fasta', '-X', '3000', '-v', '--split-spot'])
        if res is 0:
            self.fasta_dumped = True

        # Delete .sra.
        # os.remove(os.path.join(paths['ncbi'], 'sra', self.name + '.sra'))
        # self.sra_deleted = True

        # Call glistmaker.
        res = self.call([
            'glistmaker', os.path.join(paths['fasta'], self.name + '.fasta'), '-w', '25', '-o',
            os.path.join(paths['list'], self.name + '.list'), '-D'
        ])
        if res is 0:
            self.list_created = True

        # Delete fasta.
        # os.remove(os.path.join(paths['fasta'], 'fasta', self.name + '.fasta'))

        # Call glistquery.
        proc = subprocess.Popen(['glistquery', ''], stdout=subprocess.PIPE)
        while True:
            line = proc.stdout.readline()
            if line != '':
                # the real code does filtering here
                print "test:", line.rstrip()
            else:
                break

        # Write glistquery results.

        # Delete .list
        logger.info('Processed %s | %d in processing queue', self.name, q_process.qsize())


def downloader():
    while True:
        job = q_download.get()
        job.fetch()
        q_process.put(job)  # Add to processing queue if slot available. Otherwise block.

        # Keep the lock until job is in process-queue.
        # Keeps process queue from joining prematurely.
        q_download.task_done()


def processor():
    while True:
        job = q_process.get()
        job.process()
        q_process.task_done()


q_download = Queue()
q_process = Queue(10)
paths = dict()


@click.command()
@click.argument('run_table', type=click.File())
@click.argument('query_list', type=click.File())
@click.option('--data_root', '-d', default='/data', type=click.Path(exists=True),
              help='Directory for outputs and temp files.')
@click.option('--ncbi_root', '-n', default='/data/ncbi', type=click.Path(exists=True),
              help='The ncbi data directory. Can be configured from ~/.ncbi/user-settings.mkfg')
def main(run_table, query_list, data_root, ncbi_root):
    global paths

    paths = setup_tree(data_root)
    paths['ncbi'] = ncbi_root
    add_file_logger()

    check_bins()

    # TODO: remove sra lock and cache files before run

    with run_table as tsv:
        reader = csv.reader(tsv, dialect="excel-tab")
        next(reader, None)  # Skip header
        for line in reader:
            name = line[8]
            q_download.put(Job(name))

    print q_download.qsize()

    # spawn worker threads
    t_downloader = Thread(target=downloader)
    t_downloader.daemon = True
    t_downloader.start()

    t_downloader2 = Thread(target=downloader)
    t_downloader2.daemon = True
    t_downloader2.start()

    t_processor = Thread(target=processor)
    t_processor.daemon = True
    t_processor.start()

    # Block until downloads empty.
    q_download.join()

    # Block until everything processed.
    q_process.join()


if __name__ == '__main__':
    main()
