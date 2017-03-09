import os
import os.path
import logging
from logging.handlers import TimedRotatingFileHandler


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


def check_bins(logger):
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


def add_file_logger(paths, logger):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh = TimedRotatingFileHandler(os.path.join(paths['logs'], 'log'), when='midnight', backupCount=7)
    fh.setFormatter(formatter)
    fh.setLevel(logging.INFO)
    fh.suffix = "%Y-%m-%d"
    logger.addHandler(fh)
