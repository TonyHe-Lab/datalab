#!/usr/bin/env python3
"""
Historical Data Backfill Tool for Medical Work Orders.

This script processes historical data from Snowflake, enriches it with AI insights,
and loads it into PostgreSQL for analysis and search.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.etl.historical_processor import HistoricalProcessor, BackfillConfig
from src.utils.config import load_config


def setup_logging(verbose: bool = False):
    """Configure logging."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("backfill.log")],
    )


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Historical Data Backfill Tool for Medical Work Orders"
    )

    parser.add_argument(
        "--start-date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
        help="Start date for historical data (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--end-date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
        help="End date for historical data (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for processing (default: 1000)",
    )

    parser.add_argument(
        "--max-records", type=int, help="Maximum number of records to process"
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run mode (no database writes)"
    )

    parser.add_argument(
        "--resume", action="store_true", help="Resume from last checkpoint"
    )

    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=10000,
        help="Checkpoint interval in records (default: 10000)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument("--no-ai", action="store_true", help="Disable AI processing")

    parser.add_argument(
        "--no-embeddings", action="store_true", help="Disable embedding generation"
    )

    return parser.parse_args()


def main():
    """Main entry point for backfill tool."""
    args = parse_arguments()
    setup_logging(args.verbose)

    logger = logging.getLogger(__name__)
    logger.info("Starting historical data backfill tool")

    try:
        # Load configuration
        config = load_config()

        # Create Snowflake and PostgreSQL configurations
        snowflake_config = config.snowflake
        postgres_config = config.postgres

        # Create backfill configuration
        backfill_config = BackfillConfig(
            start_date=args.start_date,
            end_date=args.end_date,
            batch_size=args.batch_size,
            max_records=args.max_records,
            enable_ai_processing=not args.no_ai,
            enable_embeddings=not args.no_embeddings,
            dry_run=args.dry_run,
        )

        # Initialize processor
        processor = HistoricalProcessor(
            snowflake_config=snowflake_config,
            postgres_config=postgres_config,
            backfill_config=backfill_config,
        )

        if not processor.initialize():
            logger.error("Failed to initialize processor")
            sys.exit(1)

        # Process historical data with progress tracking
        logger.info("Starting historical data processing with progress tracking")

        try:
            # 使用新的进度跟踪方法处理数据
            processor.process_with_progress_tracking(resume=args.resume)

            logger.info("=" * 60)
            logger.info("BACKFILL COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)

            # 清理
            processor.cleanup()

            logger.info("Backfill tool completed successfully")

        except KeyboardInterrupt:
            logger.info("Backfill interrupted by user")
            processor.cleanup()
            sys.exit(0)

    except KeyboardInterrupt:
        logger.info("Backfill interrupted by user")
        if "processor" in locals():
            processor.cleanup()
        sys.exit(0)

    except Exception as e:
        logger.error(f"Backfill failed with error: {e}")
        if "processor" in locals():
            processor.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
