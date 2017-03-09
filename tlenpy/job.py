import subprocess
import os


class Job:
    logger = None
    q_download = None
    q_process = None
    paths = None

    def __init__(self, name):
        self.name = name
        self.sra_downloaded = False
        self.sra_deleted = False
        self.fasta_dumped = False
        self.fasta_deleted = False
        self.list_created = False
        self.list_deleted = False
        self.result_dumped = False

    @classmethod
    def set_logger(cls, val):
        cls.logger = val

    @classmethod
    def set_q_download(cls, val):
        cls.q_download = val

    @classmethod
    def set_q_process(cls, val):
        cls.q_process = val

    @classmethod
    def set_paths(cls, val):
        cls.paths = val

    @classmethod
    def call(cls, command):
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            # If we don't need real time logging, we could just use p.communicate.
            out = p.stdout.readline()
            if out.rstrip('\n'):
                cls.logger.info(out.rstrip('\n'))
            err = p.stderr.readline()
            if err.rstrip('\n'):
                cls.logger.error(err.rstrip('\n'))
            if not err and not out:
                cls.logger.debug("Breaking out of std capture loop!")
                break
        p.wait()
        return p.returncode

    def fetch(self):
        # Call prefetch
        res = self.call(['prefetch', self.name, '-v', '-L', '5'])
        if res is 0:
            self.sra_downloaded = True
            self.logger.info('Fetched %s | %d in download queue', self.name, self.q_download.qsize())
        else:
            self.logger.error('Fetching %s failed!', self.name)

    def process(self):
        # Call fastq-dump.

        res = self.call(
            ['fastq-dump', self.name, '-O', self.paths['fasta'], '--fasta', '-X', '3000', '-v', '--split-spot'])
        if res is 0:
            self.fasta_dumped = True

        # Delete .sra.
        # os.remove(os.path.join(paths['ncbi'], 'sra', self.name + '.sra'))
        # self.sra_deleted = True

        # Call glistmaker.
        res = self.call([
            'glistmaker', os.path.join(self.paths['fasta'], self.name + '.fasta'), '-w', '25', '-o',
            os.path.join(self.paths['list'], self.name + '.list'), '-D'
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
        self.logger.info('Processed %s | %d in processing queue', self.name, self.q_process.qsize())
