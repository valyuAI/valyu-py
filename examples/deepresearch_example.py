"""
Valyu DeepResearch SDK Example
"""
import os
from valyu import Valyu
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    print("=== Valyu DeepResearch SDK Example ===\n")

    # Initialize Valyu client
    valyu = Valyu(api_key=os.getenv("VALYU_API_KEY"))

    try:
        # Example 1: Basic research task
        print("1. Creating a basic research task...")
        task = valyu.deepresearch.create(
            input="What are the key differences between RAG and fine-tuning for LLMs?",
            model="lite",
            output_formats=["markdown"],
        )

        if not task.success:
            print(f"Failed to create task: {task.error}")
            return

        print(f"✓ Task created: {task.deepresearch_id}")
        print(f"  Status: {task.status}")
        print(f"  Model: {task.model}\n")

        # Example 2: Wait for completion with progress updates
        print("2. Waiting for task completion...")

        def on_progress(status):
            if status.progress:
                print(
                    f"   Progress: Step {status.progress.current_step}/{status.progress.total_steps}"
                )
            print(f"   Status: {status.status}")

        result = valyu.deepresearch.wait(
            task.deepresearch_id,
            poll_interval=5,
            max_wait_time=600,  # 10 minutes
            on_progress=on_progress,
        )

        if not result.success:
            print(f"Task failed: {result.error}")
            return

        print("\n✓ Research completed!")
        print(f"  Status: {result.status}")
        if result.completed_at:
            from datetime import datetime

            try:
                print(
                    f"  Completed at: {datetime.fromtimestamp(result.completed_at).strftime('%Y-%m-%d %H:%M:%S')}"
                )
            except:
                print(f"  Completed at: {result.completed_at}")

        # Display output
        if result.output:
            print("\n=== Research Output ===")
            print(result.output[:500] + "...\n")

        # Display sources
        if result.sources and len(result.sources) > 0:
            print(f"\n=== Sources ({len(result.sources)}) ===")
            for i, source in enumerate(result.sources[:5]):
                print(f"{i + 1}. {source.title}")
                print(f"   URL: {source.url}")
            if len(result.sources) > 5:
                print(f"   ... and {len(result.sources) - 5} more sources")

        # Display usage and cost
        if result.usage:
            print("\n=== Cost Breakdown ===")
            print(f"  Search cost: ${result.usage.search_cost:.4f}")
            print(f"  Contents cost: ${result.usage.contents_cost:.4f}")
            print(f"  AI cost: ${result.usage.ai_cost:.4f}")
            print(f"  Compute cost: ${result.usage.compute_cost:.4f}")
            print(f"  Total cost: ${result.usage.total_cost:.4f}")

        # Display images if any
        if result.images and len(result.images) > 0:
            print(f"\n=== Generated Images ({len(result.images)}) ===")
            for i, img in enumerate(result.images):
                print(f"{i + 1}. {img.title} ({img.image_type})")
                print(f"   URL: {img.image_url}")

        # PDF URL if available
        if result.pdf_url:
            print("\n=== PDF Report ===")
            print(f"  Download: {result.pdf_url}")

        print("\n=== Example completed successfully! ===")

    except Exception as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
