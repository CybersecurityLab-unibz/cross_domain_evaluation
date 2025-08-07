# Code for the fine-tuning of the models.

The structure of the data folder is expected to be
```commandline
data
    --ID
      --none
      --balanced
      --balancedPerDataset
      --weightedLoss
    --TOD
      --none
      --balanced
      --balancedPerDataset
      --weightedLoss
    --GOD
      --none
      --balanced
      --balancedPerDataset
      --weightedLoss
```

### fine-tune
```commandline
python main.py \
    --mode="train" \
    --weighted-loss=<"True"|"False"> \
    --path-data=<path-data> \
    --path-results=<path-results>
```

### validation/testing 
```commandline
python main.py \
    --mode="test" \
    --path-data=<path-data> \
    --path-results=<path-results> \
    --file-name-test=<"val.csv"|"test.csv">
```

### cross-validation
Can only be executed once all the validation and testing steps have been completed!

```commandline
python main.py \
    --mode="cross-val" \
    --path-data=<path-data> \
    --path-results=<path-results>
```
