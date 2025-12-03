# data/ Directory

This folder contains the behavioral analysis data for the project.

## Directory Structure

```
data/
├── BlackAnimals/          # DeepLabCut pose estimation CSVs (black strain)
├── WhiteAnimals/          # DeepLabCut pose estimation CSVs (white strain)
├── dlc_table_*.csv        # Metadata table (optional, for CSV fallback)
└── dlc_table_sample.csv   # Sample metadata for testing
```

## Data Sources

- **Pose estimation data**: Download from [Harvard Dataverse](https://doi.org/10.7910/DVN/G8CBKJ)
- **Metadata**: Export from PostgreSQL or use CSV fallback

## Setup After Download

After downloading the archive from Dataverse, extract it and move the `BlackAnimals/` and `WhiteAnimals/` directories one level up into the `data/` directory:

```bash
cd /path/to/GhrelinBehaviorQuantification/data
tar -xzf Animal_behavior_DLC_Filtered.tar.gz
mv Animal_behavior_DLC_Filtered/BlackAnimals ./
mv Animal_behavior_DLC_Filtered/WhiteAnimals ./
rm -rf Animal_behavior_DLC_Filtered
```

**Note**: `BlackAnimals/` and `WhiteAnimals/` are listed in `.gitignore` and should not be committed to the repository.

---

*See the main README.md for complete setup and usage instructions.*