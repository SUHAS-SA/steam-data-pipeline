import sys
import argparse
from src.extractor import SteamExtractor
from src.transformer import SteamDataTransformer
from src.db_loader import DatabaseLoader

def run_pipeline(stage="all"):
    print("=" * 60)
    print(f" STEAM DATA PIPELINE ORCHESTRATOR - Stage: {stage.upper()}")
    print("=" * 60)

    if stage in ["all", "extract"]:
        print("\n--- STAGE 1: Data Extraction ---")
        extractor = SteamExtractor()
        extractor.extract_new_games()

    if stage in ["all", "transform"]:
        print("\n--- STAGE 2: Data Transformation & SQL Generation ---")
        transformer = SteamDataTransformer()
        transformer.transform_to_sql()

    if stage in ["all", "load"]:
        print("\n--- STAGE 3: Database Load ---")
        loader = DatabaseLoader()
        loader.load_sql_files()

    print("\n" + "=" * 60)
    print(" PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Steam Data Extraction and Storage Pipeline CLI")
    parser.add_argument(
        "--stage", 
        choices=["all", "extract", "transform", "load"], 
        default="all",
        help="Specify pipeline execution stage (default: all)"
    )
    args = parser.parse_args()
    run_pipeline(stage=args.stage)

if __name__ == "__main__":
    main()
