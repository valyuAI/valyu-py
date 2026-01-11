"""
Batch API Example - Bulk Deep Research Tasks

This example demonstrates how to use the Batch API to run multiple
deep research tasks in parallel with efficient resource management.
"""

from valyu import Valyu
from valyu.types.deepresearch import BatchTaskInput, SearchConfig
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Valyu client
client = Valyu(api_key=os.getenv("VALYU_API_KEY"))


def basic_batch_example():
    """Create a batch and add tasks manually."""
    print("=== Basic Batch Example ===\n")

    # 1. Create a new batch
    print("Creating batch...")
    batch = client.batch.create(
        name="Market Research Batch",
        mode="fast",  # Use 'mode' instead of 'model' (preferred)
        output_formats=["markdown"],
    )

    if not batch.success:
        print(f"Error creating batch: {batch.error}")
        return

    print(f"Batch created: {batch.batch_id}")
    print(f"Status: {batch.status}\n")

    # 2. Add tasks to the batch
    print("Adding tasks...")
    tasks = [
        {
            "query": "What are the latest trends in AI?"
        },  # Use 'query' instead of 'input' (preferred)
        {"query": "Summarize recent developments in quantum computing"},
        {"query": "What is the current state of renewable energy?"},
    ]

    add_response = client.batch.add_tasks(batch.batch_id, tasks)

    if not add_response.success:
        print(f"Error adding tasks: {add_response.error}")
        return

    print(f"Added {add_response.added} tasks")
    print(f"Task IDs: {add_response.task_ids}\n")

    # 3. Check batch status
    print("Checking batch status...")
    status = client.batch.status(batch.batch_id)

    if status.success and status.batch:
        print(f"Batch: {status.batch.batch_id}")
        print(f"Status: {status.batch.status}")
        print(f"Counts: {status.batch.counts.dict()}")
        print(
            f"Cost: ${status.batch.cost:.4f}\n"
        )  # Use 'cost' instead of 'usage.total_cost' (preferred)


def advanced_batch_example():
    """Create batch with custom task configurations."""
    print("=== Advanced Batch Example ===\n")

    # Create batch with custom settings and search parameters
    print("Creating batch with custom settings...")
    batch = client.batch.create(
        name="Competitor Analysis",
        mode="heavy",  # Use 'mode' instead of 'model' (preferred)
        output_formats=["markdown", "pdf"],
        search={
            "search_type": "all",
            "included_sources": ["web", "finance"],
            "excluded_sources": ["patent"],  # Show excluded_sources
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "category": "technology",  # Show category filter
        },
        brand_collection_id="brand_123",  # Show brand_collection_id
        metadata={"project": "Q4-2024", "team": "research"},
    )

    if not batch.success:
        print(f"Error: {batch.error}")
        return

    print(f"Batch ID: {batch.batch_id}\n")

    # Add tasks with custom configurations
    tasks = [
        BatchTaskInput(
            id="task-1",
            query="Analyze OpenAI's latest product launches",  # Use 'query' instead of 'input' (preferred)
            strategy="Focus on technical capabilities and market impact",
            urls=["https://openai.com/blog"],
            metadata={"priority": "high", "category": "competitor"},
        ),
        BatchTaskInput(
            id="task-2",
            query="Analyze Anthropic's Claude AI capabilities",
            strategy="Focus on safety features and enterprise adoption",
            metadata={"priority": "high", "category": "competitor"},
        ),
        BatchTaskInput(
            id="task-3",
            query="What are Google's recent AI announcements?",
            strategy="Focus on Gemini and enterprise products",
            metadata={"priority": "medium", "category": "competitor"},
        ),
    ]

    add_response = client.batch.add_tasks(batch.batch_id, tasks)

    if add_response.success:
        print(f"Added {add_response.added} tasks\n")
    else:
        print(f"Error: {add_response.error}\n")


def batch_with_search_config_example():
    """Create batch with SearchConfig object for type safety."""
    print("=== Batch with SearchConfig Example ===\n")

    # Using SearchConfig for type safety and autocomplete
    search_config = SearchConfig(
        search_type="all",
        included_sources=["academic", "web"],
        excluded_sources=["patent"],
        start_date="2024-01-01",
        end_date="2024-12-31",
        category="technology",  # Show category filter
    )

    batch = client.batch.create(
        name="Academic Research Q4 2024",
        mode="heavy",  # Use 'mode' instead of 'model' (preferred)
        search=search_config,
        output_formats=["markdown"],
    )

    if not batch.success:
        print(f"Error: {batch.error}")
        return

    print(f"Batch created: {batch.batch_id}")
    print(f"Search config: {search_config.dict(exclude_none=True)}\n")

    # Add tasks
    tasks = [
        {
            "query": "Recent advances in quantum computing"
        },  # Use 'query' instead of 'input' (preferred)
        {"query": "Latest developments in AI safety research"},
    ]

    add_response = client.batch.add_tasks(batch.batch_id, tasks)
    if add_response.success:
        print(f"Added {add_response.added} tasks\n")


def create_and_run_example():
    """Use the convenience method to create and run a batch."""
    print("=== Create and Run Example ===\n")

    tasks = [
        {
            "query": "What is the latest in generative AI?"
        },  # Use 'query' instead of 'input' (preferred)
        {"query": "Summarize recent ML frameworks"},
        {"query": "What are the top AI startups in 2024?"},
    ]

    print("Creating batch and adding tasks...")
    batch = client.batch.create_and_run(
        tasks=tasks,
        name="Quick Research Batch",
        mode="fast",  # Use 'mode' instead of 'model' (preferred)
        wait=False,  # Set to True to wait for completion
    )

    if batch.success:
        print(f"Batch created: {batch.batch_id}")
        print(f"Status: {batch.status}\n")
    else:
        print(f"Error: {batch.error}\n")


def wait_for_completion_example():
    """Create a batch and wait for it to complete."""
    print("=== Wait for Completion Example ===\n")

    tasks = [
        {
            "query": "What is CRISPR technology?"
        },  # Use 'query' instead of 'input' (preferred)
        {"query": "Explain gene editing advancements"},
    ]

    # Create batch
    batch = client.batch.create(
        name="Gene Editing Research", mode="fast"
    )  # Use 'mode' instead of 'model' (preferred)

    if not batch.success:
        print(f"Error: {batch.error}")
        return

    # Add tasks
    client.batch.add_tasks(batch.batch_id, tasks)

    # Wait for completion with progress updates
    print(f"Waiting for batch {batch.batch_id} to complete...")

    def on_progress(status):
        if status.success and status.batch:
            counts = status.batch.counts
            print(
                f"Progress: {counts.completed + counts.failed + counts.cancelled}/{counts.total} "
                f"(Running: {counts.running}, Queued: {counts.queued})"
            )

    try:
        final_status = client.batch.wait_for_completion(
            batch.batch_id,
            poll_interval=10,
            max_wait_time=3600,
            on_progress=on_progress,
        )

        if final_status.success and final_status.batch:
            print(f"\nBatch completed!")
            print(f"Final status: {final_status.batch.status}")
            print(
                f"Total cost: ${final_status.batch.cost:.4f}"
            )  # Use 'cost' instead of 'usage.total_cost' (preferred)

    except TimeoutError as e:
        print(f"\nTimeout: {e}")
    except ValueError as e:
        print(f"\nError: {e}")


def list_tasks_example():
    """List all tasks in a batch."""
    print("=== List Tasks Example ===\n")

    # Create and populate a batch
    batch = client.batch.create(
        name="Test Batch", mode="fast"
    )  # Use 'mode' instead of 'model' (preferred)
    tasks = [
        {
            "id": "custom-1",
            "query": "First task",
        },  # Use 'query' instead of 'input' (preferred)
        {"id": "custom-2", "query": "Second task"},
        {"id": "custom-3", "query": "Third task"},
    ]
    client.batch.add_tasks(batch.batch_id, tasks)

    # List all tasks
    print(f"Listing tasks for batch {batch.batch_id}...")
    tasks_response = client.batch.list_tasks(batch.batch_id)

    # Example: List tasks with filtering and pagination
    print("\nListing completed tasks only...")
    completed_tasks = client.batch.list_tasks(
        batch.batch_id,
        status="completed",  # Filter by status
        limit=10,  # Limit results
    )

    if tasks_response.success and tasks_response.tasks:
        print(f"Found {len(tasks_response.tasks)} tasks:\n")
        for task in tasks_response.tasks:
            print(f"  - {task.batch_task_id or task.deepresearch_id}")
            print(f"    Query: {task.query}")
            print(f"    Status: {task.status}")
            print()
    else:
        print(f"Error: {tasks_response.error}")


def list_batches_example():
    """List all batches."""
    print("=== List Batches Example ===\n")

    response = client.batch.list(limit=10)

    if response.success and response.batches:
        print(f"Found {len(response.batches)} batches:\n")
        for batch in response.batches:
            print(f"  - {batch.batch_id}")
            print(f"    Name: {batch.name or 'Unnamed'}")
            print(f"    Status: {batch.status}")
            print(
                f"    Tasks: {batch.counts.total} total, {batch.counts.completed} completed"
            )
            print(
                f"    Cost: ${batch.cost:.4f}"
            )  # Use 'cost' instead of 'usage.total_cost' (preferred)
            print()
    else:
        print(f"Error: {response.error}")


def cancel_batch_example():
    """Cancel a running batch."""
    print("=== Cancel Batch Example ===\n")

    # Create a batch
    batch = client.batch.create(
        name="Cancelable Batch", mode="fast"
    )  # Use 'mode' instead of 'model' (preferred)
    tasks = [
        {"query": f"Task {i}"} for i in range(5)
    ]  # Use 'query' instead of 'input' (preferred)
    client.batch.add_tasks(batch.batch_id, tasks)

    print(f"Created batch: {batch.batch_id}")

    # Cancel it
    print("Cancelling batch...")
    cancel_response = client.batch.cancel(batch.batch_id)

    if cancel_response.success:
        print(f"Batch cancelled: {cancel_response.message}")
        print(
            f"Cancelled {cancel_response.cancelled_count} tasks"
        )  # Show cancelled_count
    else:
        print(f"Error: {cancel_response.error}")


if __name__ == "__main__":
    print("Valyu Batch API Examples\n")
    print("=" * 50)
    print()

    # Run examples
    try:
        basic_batch_example()
        print("\n" + "=" * 50 + "\n")

        advanced_batch_example()
        print("\n" + "=" * 50 + "\n")

        create_and_run_example()
        print("\n" + "=" * 50 + "\n")

        list_tasks_example()
        print("\n" + "=" * 50 + "\n")

        list_batches_example()
        print("\n" + "=" * 50 + "\n")

        # Uncomment to test wait and cancel
        # wait_for_completion_example()
        # cancel_batch_example()

    except Exception as e:
        print(f"Error: {e}")
