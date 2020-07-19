# cologne-trees-data
Create dataset of trees in Cologne, Germany.

## About
There are (as of now) 2 official datasets (from 2017 and 2020) about the city tree situation in Cologne (Germany), published by the city. Unfortunately, these datasets are far from satisfying in different data scientific regards.    
Hence, this process chain in order to address these issues by cleaning up and enriching the data.    

## Usage
Processed datasets can be found in /data/exports    
- trees_cologne.jsonln.tar.gz
- trees_cologne_reduced.jsonln.tar.gz

Both sets are stored as JSON line. For information about created data and how the original data is processed, enriched and stored, please refer to:    
[dataschema.md](https://github.com/zushicat/cologne-trees-data/blob/master/dataschema.md)



**If you like to process the data on your own**, please place following official "Baumkataster" csv datasets

- [Bestand_Einzelbaeume_Koeln_0.csv](https://offenedaten-koeln.de/sites/default/files/Bestand_Einzelbaeume_Koeln_0.csv) (latest version: 02/2017)
- [20200610_Baumbestand_Koeln.csv](https://offenedaten-koeln.de/sites/default/files/20200610_Baumbestand_Koeln.csv) (latest version: 06/2020)    

published by Stadt Köln under Creative Commons Namensnennung 3.0 DE in https://offenedaten-koeln.de/dataset/baumkataster-koeln    
in /data/original_data and keep the file naming.

Install the python environment    
```
$ pipenv install
```
and change into the envornment shell
```
$ pipenv shell
```

You can exit the shell with
```
$ exit
```

Change into /src and start the process
```
$ python create_data.py
```
The script takes about 35 minutes. (See details about the process chain in the top comment of this script.)