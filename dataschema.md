# Data schema
Information about how the data is processed and stored.    

The resulting data is based on 2 official "Baumkataster" datasets published by the City of Cologne, Germany, but is heavily modified and enriched.    
 
This is due to incomplete and/or unreliable (resp. implausible) data in the original datasets. Also, both datasets had to be merged (with a record of dataset occurrence) to determine tree existence in the past and the present (meaning: is a tree cut down between 2017 and 2020 or still existing).

**Note**    
The file trees_cologne_reduced.json.tar.gz is a very reduced version of trees_cologne.json.tar.gz, suitable i.e. web applications where lower file sizes is quite important. (See example at the bottom of this page.)   


There are 7 main objects:
- base_info
- geo_info
- tree_taxonomy
- tree_measures
- tree_age
- found_in_dataset
- predictions

Additionally the data completeness is noted:
- dataset_completeness
- base_info_completeness
- tree_taxonomy_completeness
- tree_measures_completeness
- tree_age_completeness

### base_info
Example:
```
"base_info": {
    "object_type": "building/school/dormitory (home) building",
    "tree_nr": "G15",
    "year_planting": 1991
}
```

**object_type**    
There are different situations defined by the responsible authority which can be found here:    
[object_types.json](https://github.com/zushicat/cologne-trees-data/blob/master/data/meta/object_types.json)    
Here, the english (translated) version is used.

**tree_nr**   
This is no ID.     
Please refer to https://offenedaten-koeln.de/dataset/baumkataster-koeln

**year_planting**    
The Baumkataster datasets have different definitions regarding age information of a tree. The 2017 dataset uses estimated age whereas the 2020 dataset provides the estimated year the tree was planted.    
Therefore, given a mean age of 10 years when a city tree is planted, the 2017 age estimation is recalculated to the year of planting.
**But** the age information of individual is quite unreliable (see below: tree_age).


### geo_info
Example:
```
"geo_info": {
    "utm_x": 360440,
    "utm_y": 5647594,
    "lat": 50.96302922980272,
    "lng": 7.012601080967529,
    "suburb": "Mülheim",
    "suburb_id": "901",
    "district": "Mülheim",
    "district_id": "9"
}
```

**utm_x/utm_y**    
Geoinfo taken from the datasets.    

**lat/lng**    
Latitude and longitude values, derived from utm x and y.    

**suburb/district**    
Derived from a polygon match of Cologne suburbs and the geoinfo.    
See geojson file [cologne_districts_polygons.geojson](https://github.com/zushicat/cologne-trees-data/blob/master/data/geo_data/cologne_districts_polygons.geojson)


### tree_taxonomy
Example:
```
"tree_taxonomy": {
    "genus": "Quercus",
    "genus_name_german": "Eichen",
    "species": "robur",
    "type": null,
    "name_german": [
      "Sommer-Eiche",
      "Stieleiche"
    ]
}
```

**genus/species/type/name_german**
Taken from the original data

**genus_name_german**
Derived german name of genus (as defined in wikidata.org)    
See: [genus_name_german.json](https://github.com/zushicat/cologne-trees-data/blob/master/data/meta/genus_name_german.json)


### tree_measures
Example:
```
"tree_measures": {
    "height": 12,
    "treetop_radius": 10,
    "bole_radius": 45
}
```

**height/treetop_radius/bole_radius**    
This data is taken from the datasets. Checks on samples showed that, given a tree occured in both datasets, the measures didn't change. Meaning: according to those samples, tree growth was not taken into any account in the original 2020 dataset. (You might want to keep that in mind.)    


### tree_age    
Example:    
```
"tree_age": {
    "year_sprout": 1975,
    "age_in_2020": 45,
    "age_group_2020": 2
}
```

**year_sprout**    
As mentioned before, the examination of age information from the original data revealed a very high variance which makes this data too unreliable for direct aquisition. But taken as a whole (per genus), it proves sufficiant to train a regression model (X: genus, bole radius, y: year sprout) and predict the year a tree sprout when genus and bole radius are given.    

**age_in_2020**    
Derived from year_sprout (valid for 2020)    

**age_group_2020**    
There are 3 age groups (valid for 2020)    
- 0: <= 25
- 1: 26 - 40
- 2: \> 40


### found_in_dataset    
Example:    
```
"found_in_dataset": {
    "2017": true,
    "2020": true
}
```

**2017/2020**
Bool record if a tree occured in respective dataset. (If 2020 is false, this might be an indicator that this tree is cut down.)


### predictions
Example:
```
"predictions": {
    "by_radius_prediction": {
        "genus": {
            "prediction": "Quercus",
            "probability": 0.53
        },
        "age_group": {
            "prediction": 2,
            "probability": 0.64
        },
        "year_sprout": {
            "prediction": 1977,
            "probability": 0.36
        }
    }
}
```

**by_radius_prediction**
There are trees without information about genus and measures to estimate the age by regression. Therefore, trees in a 50 meter radius around a respective tree are clustered (seperately for each prediction) and the most dominant cluster label is assigned.    

Although this method (which is basiccally "birds of a feather flock together") has its obvious and inherant limitations it's still way better than no data at all.    
(Hence the additional probability which is the percentage of the "winning" cluster trees in regard of the overall trees within the examined radius.)


## Example 1
```
{
  "tree_id": "aea89244-1dc9-435c-ad71-973739af2a0d",
  "dataset_completeness": 1,
  "base_info_completeness": 1,
  "tree_taxonomy_completeness": 1,
  "tree_measures_completeness": 1,
  "tree_age_completeness": 1,
  "base_info": {
    "object_type": "street/court (plaza)",
    "tree_nr": "P14",
    "year_planting": 2002
  },
  "geo_info": {
    "utm_x": 359965,
    "utm_y": 5648769,
    "lat": 50.973473811608784,
    "lng": 7.005388858959242,
    "suburb": "Mülheim",
    "suburb_id": "901",
    "district": "Mülheim",
    "district_id": "9"
  },
  "tree_taxonomy": {
    "genus": "Catalpa",
    "genus_name_german": "Trompetenbäume",
    "species": "bignonioides",
    "type": "Nana",
    "name_german": [
      "Kugel-Trompetenbaum"
    ]
  },
  "tree_measures": {
    "height": 4,
    "treetop_radius": 6,
    "bole_radius": 15
  },
  "tree_age": {
    "year_sprout": 1989,
    "age_in_2020": 31,
    "age_group_2020": 1
  },
  "found_in_dataset": {
    "2017": true,
    "2020": true
  },
  "predictions": null
}
```

## Example 2: tree with sparse information and predictions
```
{
  "tree_id": "1204082d-767b-4442-a2f5-2a35c8455609",
  "dataset_completeness": 0.4,
  "base_info_completeness": 1,
  "tree_taxonomy_completeness": 0.6,
  "tree_measures_completeness": 0,
  "tree_age_completeness": 0,
  "base_info": {
    "object_type": "street/court (plaza)",
    "tree_nr": "52G",
    "year_planting": 1992
  },
  "geo_info": {
    "utm_x": 362702,
    "utm_y": 5652041,
    "lat": 51.00353916397048,
    "lng": 7.043112678206608,
    "suburb": "Dünnwald",
    "suburb_id": "907",
    "district": "Mülheim",
    "district_id": "9"
  },
  "tree_taxonomy": {
    "genus": "Acer",
    "genus_name_german": "Ahorne",
    "species": null,
    "type": null,
    "name_german": [
      "Ahorn"
    ]
  },
  "tree_measures": {
    "height": null,
    "treetop_radius": null,
    "bole_radius": null
  },
  "tree_age": {
    "year_sprout": null,
    "age_in_2020": null,
    "age_group_2020": null
  },
  "found_in_dataset": {
    "2017": true,
    "2020": true
  },
  "predictions": {
    "by_radius_prediction": {
      "genus": {
        "prediction": "Acer",
        "probability": 0.35
      },
      "age_group": {
        "prediction": 2,
        "probability": 0.5
      },
      "year_sprout": {
        "prediction": 1949,
        "probability": 0.27
      }
    }
  }
}
```

## Example 3: reduced tree data (from trees_cologne_reduced.json.tar.gz)
```
{
  "tree_id": "106f2fe2-19b9-4d1a-a156-937c7c278657",
  "district_number": "9",
  "lat": 50.997211209450896,
  "lng": 6.977334634247912,
  "genus": "Fraxinus",
  "in_dataset_2020": true,
  "age_group": 2
}
```

The reduced dataset substitutes missing age_group and genus information with predicted values with a probability >= 0.5.