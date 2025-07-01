# Execution examples 
In the following, execution examples are provided, which help the reader to understand how the interaction with each function is intended. Furthermore, the python files contains a function called `parse_args` which can be further leveraged to understand how the individual pieces work. 


### Extract functions from code
```{cli}
python extract_data_from_repositories.py 
    --path-repos <path-all_repositories> 
    --path-output <output-path-repositories>
```

### Run SemGrep
```{cli}
semgrep 
    -c r/php 
    --include="*.php" 
    --no-git-ignore 
    --json 
    --output 
    ./semgrepruns/<project_name>.json 
    ./<output-path-repositories>/<project_name>
```

### Run SonarQube

Start docker and SonarQube server.
Create a quality profile and activate all rules which are not depricated, set it as a default
Create a project
Run the command 

```commandline
sonar-scanner \
  -Dsonar.projectKey=<project_name> \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.token=<token>
```

```
python extract_sonarqube.py 
    --username admin 
    --password <pwd> 
    --host localhost 
    --port 9000 
    --output-path <path-sonarqube-runs> 
    --project-key <project_name> 
```

### add information
```
python add_information_semgrep.py --input-path <path-intermediat-csv> --path-semgrep <path-semgrep-results> --path-output <output-path>
python add_information_sonarqube.py --input-path <path-intermediat-csv> --path-semgrep <path-sonarqube-results> --path-output <output-path>
```

### extract into single files
```commandline
python export_into_single_files.py 
    --path-oss datasets/<dataset>.csv 
    --path-output single_files/
```

### pmd-cpd
```commandline
pmd cpd \
  --minimum-tokens 30 \
  --language php \
  --format csv \
  --dir <input-path-single-functions> \
  --encoding UTF-8 \
  > <output-path>
```

### remove duplicate instances
```commandline
python remove_duplicates.py --path <path-intermediat-csv> --path-pmd-cpd <path-pmd-cpd-results>
```

### mutate dataset for fine-tuning
The corresponding flags can be found in the function `parse_args`, which allows to handle the mutation of the data according to the experiments conducted in RQ1.
```commandline
python extract_datasets_for_fine_tuning.py --path-input datasets/<dataset>.csv
```
