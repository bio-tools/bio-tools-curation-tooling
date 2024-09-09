# bio-tools-curation-tooling

The repo collect scripts and tools for aiding in the curation of new tools, e.g. coming from Pub2Tools and EdamMapper


## Tutorials

The file _workflow_tutorial.ipynb_ includes a detailed tutorial on how to implement the workflow after running Pub2Tools for a specific month (see [Running Pub2Tools for one month](#running-pub2tools-for-one-month).
The workflow takes the output log from Pub2Tools, separate json files with low-priority tools and preprints as input (json files under folder **data**.


## Pub2Tools

### Installation

1. In your working directory, create a folder named "Pub2Tools". 
2. Follow the installation guide at [Install Pub2Tools](https://github.com/bio-tools/pub2tools/blob/develop/INSTALL.md).

### Running Pub2Tools for one month

1. Create folder named _month_year_
2. Copy the following command and replace the folder name /work/Pub2Tools/MONTH_YEAR and month argument YYYY_MM

```
    java -jar -Xms2048M -Xmx4096M /work/Pub2Tools/pub2tools/target/pub2tools-cli-1.1.2-SNAPSHOT.jar -all /work/Pub2Tools/MONTH_YEAR --edam http://edamontology.org/EDAM.owl --idf https://github.com/edamontology/edammap/raw/master/doc/biotools.idf --idf-stemmed https://github.com/edamontology/edammap/raw/master/doc/biotools.stemmed.idf --month YYYY-MM --seleniumFirefox /work/Pub2tools/firefox/firefox/firefox-bin
```

Usually this takes 4-5 hours to finish.

