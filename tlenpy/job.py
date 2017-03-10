import subprocess
import os


class Job:
    logger = None
    q_download = None
    q_process = None
    paths = None
    kmer_sample_path = None
    fasta_check = False
    fasta_limit = 0

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
    def set_fasta_limit(cls, val):
        cls.fasta_limit = val

    @classmethod
    def set_fasta_check(cls, val):
        cls.fasta_check = val

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
    def set_kmer_sample_path(cls, val):
        cls.kmer_sample_path = val

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
        if self.fasta_check and os.path.exists(os.path.join(self.paths['fasta'], self.name + '.fasta')):
            self.logger.warn('%s.fasta exists!', self.name)
            self.fasta_dumped = True
            return True
        self.logger.info('Prefetching %s', self.name)
        # Call prefetch
        res = self.call(['prefetch', self.name])
        if res is 0:
            self.sra_downloaded = True
            self.logger.info('Fetched %s | %d in download queue', self.name, self.q_download.qsize())
            return True
        else:
            self.logger.error('Fetching %s failed!', self.name)
            return False

    def create_fasta(self):
        if not self.fasta_dumped:
            args = ['fastq-dump', self.name, '-O', self.paths['fasta'], '--fasta', '--split-spot']

            if self.fasta_limit:
                args.extend(['-X', str(self.fasta_limit)])

            res = self.call(args)
            if res is 0:
                self.fasta_dumped = True

    def create_glist(self):
        self.logger.info("Starting glistmaker for %s!", self.name)
        res = self.call([
            'glistmaker', os.path.join(self.paths['fasta'], self.name + '.fasta'), '-w', '25', '-o',
            os.path.join(self.paths['list'], self.name + '.list'), '-D'
        ])
        if res is 0:
            self.logger.info("List for %s created", self.name)
            self.list_created = True

    def create_glist_result(self):
        result_file_path = os.path.join(self.paths['query_result'], self.name + '.txt')
        if os.path.exists(result_file_path):
            os.remove(result_file_path)

        # Call glistquery.
        self.logger.info("Starting kmer query for %s!", self.name)
        proc = subprocess.Popen([
            'glistquery', os.path.join(self.paths['list'], self.name + '.list_25.list'), '-f', self.kmer_sample_path
        ], stdout=subprocess.PIPE)
        query_result_file = open(result_file_path, 'w+')
        while True:
            line = proc.stdout.readline()
            if line != '':
                # the real code does filtering here
                query_result_file.write(line.rstrip())
            else:
                break
        query_result_file.close()
        proc.wait()
        if proc.returncode is 0:
            self.logger.info("Query result for %s written!", self.name)
        else:
            self.logger.err("Query result for %s FAILED!", self.name)

    def process(self):
        self.logger.info('Started processing %s. PID: %d', self.name, os.getpid())

        # Call fastq-dump.
        self.create_fasta()

        # Delete .sra.
        os.remove(os.path.join(self.paths['ncbi'], 'sra', self.name + '.sra'))
        self.sra_deleted = True

        # Call glistmaker.
        self.create_glist()

        # Delete fasta.
        os.remove(os.path.join(self.paths['fasta'], self.name + '.fasta'))
        self.fasta_deleted = True

        self.create_glist_result()

        # Delete .list
        os.remove(os.path.join(self.paths['list'], self.name + '.list_25.list'))
        # TODO: more jobs here

        self.logger.info('Processed %s | %d in processing queue', self.name, self.q_process.qsize())
