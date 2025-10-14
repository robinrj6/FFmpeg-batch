#!/usr/bin/env python3
"""
CLI tool for FFmpeg Batch Video Processor
Allows interaction with the API from command line
"""

import argparse
import requests
import json
import sys
from pathlib import Path
from typing import Optional
import time


class VideoProcessorCLI:
    """Command-line interface for the video processor."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def create_job(self, input_file: str, operation: str, parameters: dict, output_file: Optional[str] = None):
        """Create a new processing job."""
        try:
            response = requests.post(
                f"{self.base_url}/jobs/",
                json={
                    "input_file": input_file,
                    "operation": operation,
                    "parameters": parameters,
                    "output_file": output_file
                }
            )
            response.raise_for_status()
            result = response.json()
            print(f"✓ Job created: {result['job_id']}")
            return result['job_id']
        except Exception as e:
            print(f"✗ Failed to create job: {e}")
            sys.exit(1)

    def create_job_from_profile(self, input_file: str, profile: str, output_file: Optional[str] = None):
        """Create a job using a profile."""
        try:
            response = requests.post(
                f"{self.base_url}/jobs/profile/",
                json={
                    "input_file": input_file,
                    "profile": profile,
                    "output_file": output_file
                }
            )
            response.raise_for_status()
            result = response.json()
            print(f"✓ Job created from profile '{profile}': {result['job_id']}")
            return result['job_id']
        except Exception as e:
            print(f"✗ Failed to create job: {e}")
            sys.exit(1)

    def create_workflow(self, input_file: str, workflow: str):
        """Create jobs from a workflow."""
        try:
            response = requests.post(
                f"{self.base_url}/jobs/workflow/",
                json={
                    "input_file": input_file,
                    "workflow": workflow
                }
            )
            response.raise_for_status()
            result = response.json()
            print(f"✓ Created {result['total_jobs']} jobs from workflow '{workflow}':")
            for job in result['jobs']:
                print(f"  - {job['job_id']} ({job['profile']})")
            return [job['job_id'] for job in result['jobs']]
        except Exception as e:
            print(f"✗ Failed to create workflow: {e}")
            sys.exit(1)

    def get_job(self, job_id: str):
        """Get job status."""
        try:
            response = requests.get(f"{self.base_url}/jobs/{job_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"✗ Failed to get job: {e}")
            sys.exit(1)

    def list_jobs(self, status: Optional[str] = None):
        """List all jobs."""
        try:
            url = f"{self.base_url}/jobs/"
            if status:
                url += f"?status={status}"

            response = requests.get(url)
            response.raise_for_status()
            jobs = response.json()

            if not jobs:
                print("No jobs found")
                return

            print(f"\n{'ID':<38} {'Status':<12} {'Operation':<20} {'Progress':<10}")
            print("-" * 85)

            for job in jobs:
                print(
                    f"{job['id']:<38} "
                    f"{job['status']:<12} "
                    f"{job['operation']:<20} "
                    f"{job['progress']:.1f}%"
                )

        except Exception as e:
            print(f"✗ Failed to list jobs: {e}")
            sys.exit(1)

    def watch_job(self, job_id: str):
        """Watch job progress in real-time."""
        print(f"Watching job {job_id}...")
        print("Press Ctrl+C to stop watching\n")

        try:
            while True:
                job = self.get_job(job_id)

                # Clear line and print status
                sys.stdout.write('\r' + ' ' * 100 + '\r')
                sys.stdout.write(
                    f"Status: {job['status']:<12} | "
                    f"Progress: {job['progress']:.1f}% | "
                    f"Operation: {job['operation']}"
                )
                sys.stdout.flush()

                if job['status'] in ['completed', 'failed', 'cancelled']:
                    print("\n")
                    if job['status'] == 'completed':
                        print(f"✓ Job completed successfully")
                        print(f"Output: {job['output_file']}")
                    elif job['status'] == 'failed':
                        print(f"✗ Job failed: {job.get('error', 'Unknown error')}")
                    else:
                        print(f"⚠ Job was cancelled")
                    break

                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\nStopped watching")

    def list_profiles(self):
        """List available profiles."""
        try:
            response = requests.get(f"{self.base_url}/profiles/")
            response.raise_for_status()
            profiles = response.json()

            print("\nAvailable Profiles:")
            print("-" * 80)
            for profile in profiles:
                print(f"\n{profile['name']}")
                print(f"  Operation: {profile['operation']}")
                print(f"  Description: {profile['description']}")

        except Exception as e:
            print(f"✗ Failed to list profiles: {e}")
            sys.exit(1)

    def list_workflows(self):
        """List available workflows."""
        try:
            response = requests.get(f"{self.base_url}/workflows/")
            response.raise_for_status()
            workflows = response.json()

            print("\nAvailable Workflows:")
            print("-" * 80)
            for workflow in workflows:
                print(f"\n{workflow['name']}")
                print(f"  Description: {workflow['description']}")
                print(f"  Jobs: {workflow['jobs']}")

        except Exception as e:
            print(f"✗ Failed to list workflows: {e}")
            sys.exit(1)

    def get_stats(self):
        """Get processing statistics."""
        try:
            response = requests.get(f"{self.base_url}/stats/")
            response.raise_for_status()
            stats = response.json()

            print("\nProcessing Statistics:")
            print("-" * 40)
            print(f"Total Jobs: {stats['queue']['total_jobs']}")
            print(f"Completed: {stats['queue']['completed_jobs']}")
            print(f"Failed: {stats['queue']['failed_jobs']}")
            print(f"Processing: {stats['queue']['processing_jobs']}")
            print(f"Queue Size: {stats['queue']['queue_size']}")
            print(f"Active Workers: {stats['queue']['active_workers']}")
            print(f"\nProfiles: {stats['profiles']}")
            print(f"Workflows: {stats['workflows']}")

        except Exception as e:
            print(f"✗ Failed to get stats: {e}")
            sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="FFmpeg Batch Video Processor CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create job command
    create_parser = subparsers.add_parser("create", help="Create a new job")
    create_parser.add_argument("input", help="Input video file path")
    create_parser.add_argument("operation", help="Operation to perform")
    create_parser.add_argument("--output", help="Output file path")
    create_parser.add_argument("--params", help="Parameters as JSON string", default="{}")

    # Profile command
    profile_parser = subparsers.add_parser("profile", help="Create job from profile")
    profile_parser.add_argument("input", help="Input video file path")
    profile_parser.add_argument("profile", help="Profile name")
    profile_parser.add_argument("--output", help="Output file path")

    # Workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Create jobs from workflow")
    workflow_parser.add_argument("input", help="Input video file path")
    workflow_parser.add_argument("workflow", help="Workflow name")

    # Status command
    status_parser = subparsers.add_parser("status", help="Get job status")
    status_parser.add_argument("job_id", help="Job ID")

    # List command
    list_parser = subparsers.add_parser("list", help="List jobs")
    list_parser.add_argument("--status", help="Filter by status")

    # Watch command
    watch_parser = subparsers.add_parser("watch", help="Watch job progress")
    watch_parser.add_argument("job_id", help="Job ID")

    # Profiles command
    subparsers.add_parser("profiles", help="List available profiles")

    # Workflows command
    subparsers.add_parser("workflows", help="List available workflows")

    # Stats command
    subparsers.add_parser("stats", help="Show processing statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cli = VideoProcessorCLI(base_url=args.url)

    # Execute command
    if args.command == "create":
        params = json.loads(args.params)
        job_id = cli.create_job(args.input, args.operation, params, args.output)
        cli.watch_job(job_id)

    elif args.command == "profile":
        job_id = cli.create_job_from_profile(args.input, args.profile, args.output)
        cli.watch_job(job_id)

    elif args.command == "workflow":
        job_ids = cli.create_workflow(args.input, args.workflow)

    elif args.command == "status":
        job = cli.get_job(args.job_id)
        print(json.dumps(job, indent=2))

    elif args.command == "list":
        cli.list_jobs(args.status)

    elif args.command == "watch":
        cli.watch_job(args.job_id)

    elif args.command == "profiles":
        cli.list_profiles()

    elif args.command == "workflows":
        cli.list_workflows()

    elif args.command == "stats":
        cli.get_stats()


if __name__ == "__main__":
    main()
