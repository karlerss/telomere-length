*work in progress*

To run on windows, use powershell: 

` docker build -t ktel .; docker run -v //f//data://data ktel python get_srr.py SraRunTable.txt kmer_sample_min.txt --check_fasta true --fasta_limit 3000;`

Make sure you mark the data directory drive as a shared drive from the docker manager app.

kmer_sample_min.txt contains:
* line 1 - the telomere k-mer
* lines 2-1319 - a random sample
* lines 1320 - 1583 - Tarmo's Alu-list
* lines 1584 - 3083 k-mers from telomere-length associated SNP-s (Variation-Locations-Homo_sapiens_Phenotype_Locations_Telomere_length.csv)

On mamba run with `nohup ... &>/dev/null &`

###Analysis

To run the analysis:

1. build the docker image from /analysis dockerfile
1. `docker run -d -p=6006:6006 -p=8888:8888 -v=//f//srv//notebooks://srv keras`
1. navigate to localhost:8888 and open the notebook