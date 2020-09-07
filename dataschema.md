# Data schema
Information about how the data is processed and stored.    

The resulting data is based on 2 official "Baumkataster" tree inventory datasets published by the City of Cologne, Germany, but is heavily modified and enriched.    
 
This is due to incomplete and/or unreliable (resp. implausible) data in the original datasets. Also, both datasets had to be merged (with a record of the occurrence in respective dataset) to determine tree existence in the past and the present (meaning: is a tree cut down between 2017 and 2020 or is it still existing).    

**Note**    
The record entries in both datasets have no unique id per tree and a certain tolerance regarding the physical measurement of the geographical tree location must be assumed. Therefore it should not be assumed that each entry really represents an unique tree.     
Hence, there is a process implemented where trees are merged if their distance is < 3 meter:
- if such a tree pair is existing in the same timeline (i.e. both are in dataset 2020 or only in dataset 2017): use the tree with the higher data completeness (or if equal: take any)
- if one tree of such a tree pair only occures in datasat 2017 and the other tree occures in the dataset 2020: use the "newer" tree entry occuring in the 2020 dataset


**Note**    
The file [trees_cologne_reduced.json.tar.gz](https://github.com/zushicat/cologne-trees-data/blob/master/data/exports/trees_cologne_reduced.jsonln.tar.gz) is a very reduced version of [trees_cologne.json.tar.gz](https://github.com/zushicat/cologne-trees-data/blob/master/data/exports/trees_cologne.jsonln.tar.gz), suitable for i.e. web applications where lower file size is quite important. (See example at the bottom of this page.)   


**Note**    
Regarding .tree_measures.treetop_radius and .tree_measures.bole_radius:
In the heat of the moment I wrongly named the attributes for treetop and bole (trunk) values as radius when in fact
- treetop_radius is the **diameter** of a treetop
- bole_radius is the **perimeter** of a trunk

**I will correct the naming of both attributes in the near future. Until then, please keep that in mind.**


**Note**    
There are 2 attributes regarding the tree envirnment: base_info.object_type and tree_location_type.    
The first value is directly taken from the tree inventory. After some exploration, these values don't seem to reflect the real situation with a strong bias towards "building/school/dormitory (home) building". (This value almost appears to be some kind of default.)     

Therefore, tree_location_type is introduced with an OpenStreetMap (OSM) data match of each tree (point) position regarding 3 broad environment categories.

    
    
**There are 8 main objects:**
- base_info
- geo_info
- tree_taxonomy
- tree_measures
- tree_age
- found_in_dataset
- predictions
- tree_location_type

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
This is unmodified data from the tree inventories. (Exception: year_planting for data from the 2017 dataset.)     


**object_type**    
There are different situations defined by the responsible authority which can be found here:    
[object_types.json](https://github.com/zushicat/cologne-trees-data/blob/master/data/meta/object_types.json)    
Here, the english (translated) version is being used.

**tree_nr**   
This is no ID.     
Please refer to https://offenedaten-koeln.de/dataset/baumkataster-koeln

**year_planting**    
The "Baumkataster" tree inventory datasets have different definitions regarding age information of a tree. The 2017 dataset uses estimated age whereas the 2020 dataset provides the estimated year the tree was planted.    
Therefore, given a mean age of 10 years when a city tree is planted, the 2017 age estimation is recalculated accordingly to the year of planting.    
**But** the age information in regards of individual trees is quite unreliable (see below: tree_age).


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
Derived from a polygon match of Cologne suburbs and the respective geo information properties.    
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

**Note**
Regarding .tree_measures.treetop_radius and .tree_measures.bole_radius:
In the heat of the moment I wrongly named the attributes for treetop and bole (trunk) values as radius when in fact
- treetop_radius is the **diameter** of a treetop
- bole_radius is the **perimeter** of a trunk

**I will correct the naming of both attributes in the near future. Until then, please keep that in mind.**


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
As mentioned before, the examination of age information from the original data revealed a very high variance which makes this data too unreliable for direct aquisition on individual tree. But taken as a whole (per genus), it proves sufficiant to train a regression model (X: genus, bole radius, y: year sprout) and predict the year a tree sprout when genus and bole radius are given.    

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

Although this method (which is basically "birds of a feather flock together") has its obvious and inherant limitations it's still way better than no data at all.    
(Hence the additional probability which is the percentage of the "winning" cluster trees in regard of the overall trees within the examined radius.)


### tree_location_type
Example:
```
"tree_location_type": {
    "green_spaces_agriculture": {
      "category": "green_spaces_agriculture",
      "type": "farmland",
      "name": null,
      "osm_id": 38325295,
      "wikidata_id": null
  },
  "highway": {
      "category": "highway",
      "type": "service",
      "name": null,
      "osm_id": 27090973,
      "wikidata_id": null
  }
}
```

The geolocation of each tree is matched with OpenStreetMap (OSM) data of 3 broad categories:
- **highway:** following the OSM naming convention, using **all** types of mapped ways incl. sidewalks
- **green_spaces_leisure:** green spaces occuring in mostly urban areas
- **green_spaces_agriculture:** green spaces occuring in mostly rural areas

or null


These categories are reflecting the most likely stress level of a tree environment:
- streets et.al.: high
- parks et.al.: medium
- forests et.al: low 


**Please note**    
tree_location_type allows multiple categories, because all highway (line) elements have a surrounding default buffer of approx. 5 meter, whereas the green spaces are usually defined as polygon areas. Therefore, the highway match is less accurate since this buffer is an estimation of the road width.     

In case that both green space and highway attributes occure, this indicates that a tree definitly intersects with a green space polygon, but is at least near a street environment.    
(If in doubt, you then may prefer the green space attribute, although there's certainly room for interpretation.)


Following values are requested for each respective category:
- highway
    - all
- green_spaces_leisure
    - park
    - playground
    - grass
    - recreation_ground
    - cemetery
- green_spaces_agriculture
    - allotments
    - farmland
    - forest
    - meadow
    - orchard


For detailed information about the requested OSM values, please refer to 
- https://wiki.openstreetmap.org/wiki/Key:highway
- https://wiki.openstreetmap.org/wiki/Landuse
- https://wiki.openstreetmap.org/wiki/Key:leisure



## Example 1
```
{
  "tree_id": "703c3c28-0da6-4706-b0bf-f3d2e1b7a976",
  "dataset_completeness": 0.95,
  "base_info_completeness": 1,
  "tree_taxonomy_completeness": 0.8,
  "tree_measures_completeness": 1,
  "tree_age_completeness": 1,
  "base_info": {
    "object_type": "building/school/dormitory (home) building",
    "tree_nr": "10G",
    "year_planting": 1993
  },
  "geo_info": {
    "utm_x": 358061,
    "utm_y": 5651408,
    "lat": 50.99672419050312,
    "lng": 6.977256051311555,
    "suburb": "Flittard",
    "suburb_id": "909",
    "district": "Mülheim",
    "district_id": "9"
  },
  "tree_taxonomy": {
    "genus": "Fraxinus",
    "genus_name_german": "Eschen",
    "species": "excelsior",
    "type": null,
    "name_german": [
      "Gemeine Esche"
    ]
  },
  "tree_measures": {
    "height": 9,
    "treetop_radius": 5,
    "bole_radius": 25
  },
  "tree_age": {
    "year_sprout": 1985,
    "age_in_2020": 35,
    "age_group_2020": 1
  },
  "found_in_dataset": {
    "2017": true,
    "2020": true
  },
  "predictions": null,
  "tree_location_type": {
    "green_spaces_agriculture": {
      "category": "green_spaces_agriculture",
      "type": "farmland",
      "name": null,
      "osm_id": 38325295,
      "wikidata_id": null
    },
    "highway": {
      "category": "highway",
      "type": "service",
      "name": null,
      "osm_id": 27090973,
      "wikidata_id": null
    }
  }
}
```

## Example 2: tree with sparse information and predictions
```
{
  "tree_id": "20e75116-e3b9-4123-88d2-018aef87f867",
  "dataset_completeness": 0.17,
  "base_info_completeness": 0.67,
  "tree_taxonomy_completeness": 0,
  "tree_measures_completeness": 0,
  "tree_age_completeness": 0,
  "base_info": {
    "object_type": "building/school/dormitory (home) building",
    "tree_nr": "34U",
    "year_planting": null
  },
  "geo_info": {
    "utm_x": 362364,
    "utm_y": 5647581,
    "lat": 50.963375244848244,
    "lng": 7.039987391288516,
    "suburb": "Holweide",
    "suburb_id": "904",
    "district": "Mülheim",
    "district_id": "9"
  },
  "tree_taxonomy": {
    "genus": null,
    "genus_name_german": null,
    "species": null,
    "type": null,
    "name_german": null
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
        "prediction": "Quercus",
        "probability": 0.53
      },
      "age_group": {
        "prediction": 2,
        "probability": 0.61
      },
      "year_sprout": {
        "prediction": 1980,
        "probability": 0.31
      }
    }
  },
  "tree_location_type": {
    "highway": {
      "category": "highway",
      "type": "residential",
      "name": "Burgwiesenstraße",
      "osm_id": 25496381,
      "wikidata_id": null
    }
  }
}
```

## Example 3: reduced tree data (from trees_cologne_reduced.json.tar.gz)
```
{
  "tree_id": "1537ebd5-75fb-4bd9-9c20-898f99c6d30a",
  "district_number": "9",
  "lat": 50.961181877547325,
  "lng": 7.005003979097982,
  "in_dataset_2020": true,
  "genus": "Platanus",
  "age_group": 1,
  "location_type": [
    "highway"
  ]
}
```

The reduced dataset substitutes missing age_group and genus information with predicted values with a probability >= 0.5.
