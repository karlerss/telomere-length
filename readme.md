*work in progress*

To run on windows, use powershell: 

` docker build -t ktel .; docker run -v //f//data://data ktel python get_srr.py SraRunTable.txt kmer_sample_min.txt --check_fasta true --fasta_limit 3000;`

Make sure you mark the data directory drive as a shared drive from the docker manager app.

On mamba run with `nohup ... &>/dev/null &`