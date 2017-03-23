import pymysql
import pymysql.cursors
import struct
import urllib
import xml.etree.ElementTree as ET


def get_seq(chr, min, max, expected=''):
    url = "http://genome.ucsc.edu/cgi-bin/das/hg38/dna?segment={}:{},{}".format(chr, min - 24, max + 24)
    f = urllib.urlopen(url)
    contents = f.read()
    eltree = ET.fromstring(contents)
    one = eltree.findall('./SEQUENCE/DNA')[0].text.strip()
    return one


def get_snps(snps):
    conn = pymysql.connect(host='useastdb.ensembl.org', user='anonymous',
                           passwd='', db='homo_sapiens_variation_87_38', charset='utf8')
    dbc = conn.cursor()
    dbc.execute('SET NAMES utf8;')
    dbc.execute('SET CHARACTER SET utf8;')
    dbc.execute('SET character_set_connection=utf8;')
    conn.commit()

    cursor = conn.cursor()
    cursor.execute(
        'SELECT v.name, vf.allele_string, v.ancestral_allele, v.minor_allele, sr.name as chr, vf.seq_region_start, vf.seq_region_end FROM variation v ' +
        'LEFT JOIN variation_feature vf ON vf.variation_id=v.variation_id ' +
        'LEFT JOIN seq_region sr ON sr.seq_region_id=vf.seq_region_id ' +
        'WHERE v.name in ("' + '", "'.join(snps) + '")')
    columns = cursor.description
    results = [{columns[index][0]: column for index, column in enumerate(value)} for value in cursor.fetchall()]

    return results


def get_kmers(string, k):
    kmers = []
    n = len(string)

    for i in range(0, n - k + 1):
        kmers.append(string[i:i + k])

    return kmers


def main():
    snps = get_snps(
        ['rs621559', 'rs11125529', 'rs4452212', 'rs16859140', 'rs12696304', 'rs10936599', 'rs1317082', 'rs10936601',
         'rs7680468', 'rs2736100', 'rs2098713', 'rs2736428', 'rs654128', 'rs34596385', 'rs11787341', 'rs10904887',
         'rs10466239', 'rs9419958', 'rs9420907', 'rs4387287', 'rs17653722', 'rs398652', 'rs4902100', 'rs74019828',
         'rs3027234', 'rs2162440', 'rs412658', 'rs1975174', 'rs6028466', 'rs73394838', 'rs412658', 'rs2736428',
         'rs2736428', 'rs2736428', 'rs2736428', 'rs2736428', 'rs2736428'])
    for i, snp in enumerate(snps):
        if len(snp['chr']) > 2:
            continue

        sequence = get_seq(snp['chr'], snp['seq_region_start'], snp['seq_region_end'])

        t = list(sequence)
        t[24] = snp['minor_allele']
        t = ''.join(t)
        alt_sequence = t

        kmers = get_kmers(sequence, 25)
        for i, k in enumerate(kmers):
            print "{}:25:{}\t{}".format(snp['name'], i, k.upper())

        asd = get_kmers(alt_sequence, 25)
        for l, m in enumerate(asd):
            print "ALT_{}:25:{}\t{}".format(snp['name'], l, m.upper())


if __name__ == '__main__':
    main()
