import click
import os
import os.path
import shutil
from ftplib import FTP


def setup_tree(path):
    if os.path.isabs(path):
        data_base = path
    else:
        data_base = os.path.join(os.getcwd(), path)

    if not os.path.exists(data_base):
        os.mkdir(data_base)

    if os.path.exists(os.path.join(data_base, 'tmp')):
        shutil.rmtree(os.path.join(data_base, 'tmp'))

    directories = ['sra', 'list', 'result', 'logs', 'tmp', 'fastq']

    paths = dict()

    for d in directories:
        if not os.path.exists(os.path.join(data_base, d)):
            os.mkdir(os.path.join(data_base, d))
        paths[d] = os.path.join(data_base, d)

    return paths


@click.command()
@click.argument('sra_name')
@click.option('--base', default='data', type=click.Path(), help="The data directory.")
def download_sra(sra_name, base):
    paths = setup_tree(base)
    if os.path.exists(os.path.join(paths.get('sra'), sra_name + '.sra')):
        click.echo(click.style('File already exists!', fg='green'))
        return
    ftp = FTP('ftp-trace.ncbi.nih.gov')
    ftp.login('anonymous')
    ftp.cwd('/sra/sra-instant/reads/ByRun/sra/SRR/{}/{}/'.format(sra_name[0:6], sra_name))
    file_names = ftp.nlst()
    click.echo('Started download!')
    #return
    with open(os.path.join(paths.get('tmp'), file_names[0]), 'wb') as local_file:
        ftp.retrbinary('RETR ' + file_names[0], local_file.write)

    shutil.move(os.path.join(paths.get('tmp'), file_names[0]), os.path.join(paths.get('sra'), file_names[0]))
    click.echo(click.style('Downloaded:' + sra_name, fg='green'))
    ftp.close()


if __name__ == '__main__':
    download_sra()
