"""
Command-line interface for Azure DevOps Test Manager.

This module provides the main CLI entry point for the azure-devops-test-manager tool.
"""

import argparse
import json
import sys
import csv
from datetime import datetime
from typing import Optional

from .core import AzureTestPointManager, ConfigurationError, AzureAPIError


def print_console_output(all_test_points, detailed=False):
    """Print formatted console output"""
    print(f"\n{'='*80}")
    print(f"TEST POINTS SUMMARY")
    print(f"{'='*80}")
    
    total_points = 0
    total_suites = len(all_test_points)
    
    for suite_id, suite_data in all_test_points.items():
        suite_info = suite_data['suite_info']
        test_points = suite_data['test_points']
        point_count = len(test_points)
        total_points += point_count
        
        print(f"\n📁 Suite: {suite_info['name']} (ID: {suite_id})")
        print(f"   Type: {suite_info['type']}")
        print(f"   Test Points: {point_count}")
        
        if point_count > 0:
            # Show outcome distribution
            outcomes = {}
            states = {}
            automated_count = 0
            
            for point in test_points:
                outcome = point['outcome']
                state = point['state']
                outcomes[outcome] = outcomes.get(outcome, 0) + 1
                states[state] = states.get(state, 0) + 1
                if point['automated']:
                    automated_count += 1
            
            print(f"   Outcomes: {', '.join([f'{k}: {v}' for k, v in outcomes.items()])}")
            print(f"   States: {', '.join([f'{k}: {v}' for k, v in states.items()])}")
            print(f"   Automated: {automated_count}/{point_count}")
            
            # Show first few test points
            print(f"   Test Points:")
            for i, point in enumerate(test_points[:5], 1):
                tc_name = point.get('test_case_title', point['test_case_name'])
                print(f"     {i}. Point {point['point_id']}: TC-{point['test_case_id']} - {tc_name[:60]}")
                print(f"        State: {point['state']}, Outcome: {point['outcome']}, Config: {point['configuration_name']}")
                
                if detailed and point.get('test_case_details'):
                    details = point['test_case_details']
                    print(f"        Priority: {details.get('priority', 'N/A')}, Steps: {len(details.get('steps', []))}")
                    print(f"        Automation: {details.get('automation_status', 'N/A')}")
            
            if point_count > 5:
                print(f"     ... and {point_count - 5} more test points")
    
    print(f"\n{'='*80}")
    print(f"TOTAL SUMMARY")
    print(f"{'='*80}")
    print(f"Total Suites: {total_suites}")
    print(f"Total Test Points: {total_points}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def save_json_output(all_test_points, plan_id):
    """Save results to JSON file"""
    filename = f"test_points_plan_{plan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_test_points, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Results saved to: {filename}")


def save_csv_output(all_test_points, plan_id):
    """Save results to CSV file"""
    filename = f"test_points_plan_{plan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        header = [
            'Suite ID', 'Suite Name', 'Suite Type', 'Point ID', 'Test Case ID', 
            'Test Case Name', 'State', 'Outcome', 'Configuration', 'Assigned To', 
            'Automated', 'Priority', 'Steps Count'
        ]
        writer.writerow(header)
        
        # Write data
        for suite_id, suite_data in all_test_points.items():
            suite_info = suite_data['suite_info']
            for point in suite_data['test_points']:
                row = [
                    suite_id,
                    suite_info['name'],
                    suite_info['type'],
                    point['point_id'],
                    point['test_case_id'],
                    point.get('test_case_title', point['test_case_name']),
                    point['state'],
                    point['outcome'],
                    point['configuration_name'],
                    point['assigned_to'],
                    point['automated'],
                    point.get('test_case_priority', 'N/A'),
                    point.get('steps_count', 0)
                ]
                writer.writerow(row)
    
    print(f"\n📊 CSV results saved to: {filename}")


def update_points_by_criteria(manager, plan_id, suite_id=None, outcome='Passed', 
                             filter_criteria=None, dry_run=False, comment=None):
    """Update test points based on criteria"""
    print(f"\n{'='*80}")
    print(f"{'DRY RUN - ' if dry_run else ''}UPDATING TEST POINTS")
    print(f"{'='*80}")
    print(f"Plan ID: {plan_id}")
    print(f"Suite ID: {suite_id if suite_id else 'All suites'}")
    print(f"Target Outcome: {outcome}")
    print(f"Filter Criteria: {filter_criteria if filter_criteria else 'None (all points)'}")
    print(f"{'='*80}")
    
    # Get all test points for filtering
    all_test_points = manager.list_test_points_for_plan(plan_id, suite_id)
    
    if not all_test_points:
        print("No test points found to update.")
        return {'total_updated': 0, 'total_found': 0}
    
    update_summary = {
        'total_found': 0,
        'total_eligible': 0,
        'total_updated': 0,
        'suites_processed': 0,
        'errors': []
    }
    
    for current_suite_id, suite_data in all_test_points.items():
        suite_info = suite_data['suite_info']
        test_points = suite_data['test_points']
        update_summary['total_found'] += len(test_points)
        
        # Filter points based on criteria
        eligible_points = []
        
        for point in test_points:
            # Apply filter criteria if provided
            if filter_criteria:
                meets_criteria = True
                
                # Check current outcome filter
                if 'current_outcome' in filter_criteria:
                    if point['outcome'] != filter_criteria['current_outcome']:
                        meets_criteria = False
                
                # Check automation status filter
                if 'automated' in filter_criteria:
                    if point['automated'] != filter_criteria['automated']:
                        meets_criteria = False
                
                # Check state filter
                if 'state' in filter_criteria:
                    if point['state'] != filter_criteria['state']:
                        meets_criteria = False
                
                # Check test case name contains filter
                if 'test_name_contains' in filter_criteria:
                    test_name = point.get('test_case_title', point['test_case_name']).lower()
                    if filter_criteria['test_name_contains'].lower() not in test_name:
                        meets_criteria = False
                
                if not meets_criteria:
                    continue
            
            eligible_points.append(point)
        
        update_summary['total_eligible'] += len(eligible_points)
        
        if eligible_points:
            print(f"\nSuite: {suite_info['name']} (ID: {current_suite_id})")
            print(f"  Eligible points: {len(eligible_points)}/{len(test_points)}")
            
            if dry_run:
                print(f"  [DRY RUN] Would update {len(eligible_points)} points to {outcome}")
                for point in eligible_points[:5]:  # Show first 5
                    tc_name = point.get('test_case_title', point['test_case_name'])
                    print(f"    - Point {point['point_id']}: {tc_name[:60]} (Current: {point['outcome']})")
                if len(eligible_points) > 5:
                    print(f"    - ... and {len(eligible_points) - 5} more points")
            else:
                # Perform actual updates
                for point in eligible_points:
                    try:
                        manager.update_test_point_outcome(
                            plan_id, current_suite_id, point['point_id'], outcome, comment
                        )
                        update_summary['total_updated'] += 1
                        print(f"    ✓ Updated point {point['point_id']}")
                    except AzureAPIError as e:
                        error_msg = f"Failed to update point {point['point_id']}: {e}"
                        update_summary['errors'].append(error_msg)
                        print(f"    ✗ {error_msg}")
            
            update_summary['suites_processed'] += 1
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"UPDATE SUMMARY")
    print(f"{'='*80}")
    print(f"Total Points Found: {update_summary['total_found']}")
    print(f"Eligible for Update: {update_summary['total_eligible']}")
    print(f"Successfully Updated: {update_summary['total_updated']}")
    print(f"Suites Processed: {update_summary['suites_processed']}")
    
    if update_summary['errors']:
        print(f"Errors: {len(update_summary['errors'])}")
        for error in update_summary['errors'][:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(update_summary['errors']) > 5:
            print(f"  - ... and {len(update_summary['errors']) - 5} more errors")
    
    return update_summary


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='Manage Azure DevOps test points with XML integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables (Required):
  AZURE_DEVOPS_PAT      Your Azure DevOps Personal Access Token
  AZURE_DEVOPS_ORG      Organization URL (default: https://kognifai.visualstudio.com)
  AZURE_DEVOPS_PROJECT  Project name (default: KM Commercial Marine)

Examples:
  # List test points
  azure-devops-test-manager 679333                           # List all points in plan
  azure-devops-test-manager 679333 679334                   # List points in specific suite
  azure-devops-test-manager 679333 --detailed               # List with detailed info
  azure-devops-test-manager 679333 --output json            # Save to JSON file
  
  # Update test points
  azure-devops-test-manager 679333 --update-outcome Passed                    # Mark all as Passed
  azure-devops-test-manager 679333 --update-outcome Failed --dry-run          # Preview updates
  azure-devops-test-manager 679333 --update-outcome Passed --comment "Fixed"  # Add comment
  
  # XML-based updates
  azure-devops-test-manager 679333 --from-xml test-results.xml --dry-run      # Preview XML updates
  azure-devops-test-manager 679333 --from-xml test-results.xml               # Update from XML
        """
    )
    
    parser.add_argument('plan_id', type=int, nargs='?', help='Test plan ID')
    parser.add_argument('suite_id', type=int, nargs='?', help='Optional: Test suite ID')
    parser.add_argument('--detailed', '-d', action='store_true', 
                       help='Fetch detailed test case information (slower)')
    parser.add_argument('--output', '-o', choices=['console', 'json', 'csv'], 
                       default='console', help='Output format')
    
    # Update functionality arguments
    parser.add_argument('--update-outcome', choices=['Passed', 'Failed', 'Blocked', 'NotApplicable', 
                                                    'Inconclusive', 'Timeout', 'Aborted', 'None'],
                       help='Update test points to this outcome')
    parser.add_argument('--comment', help='Comment to add when updating test points')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview what would be updated without making changes')
    
    # Filtering arguments for updates
    parser.add_argument('--filter-outcome', help='Only update points with this current outcome')
    parser.add_argument('--filter-automated', type=bool, help='Filter by automation status (true/false)')
    parser.add_argument('--filter-state', help='Only update points with this current state')
    parser.add_argument('--filter-name', help='Only update points with test names containing this text')
    
    # XML test results integration
    parser.add_argument('--from-xml', metavar='XML_FILE', 
                       help='Update test points based on test results from XML file')
    parser.add_argument('--min-score', type=int, default=80, metavar='SCORE',
                       help='Minimum fuzzy matching score (0-100) for XML matching (default: 80)')
    
    # Configuration command
    parser.add_argument('--show-config', action='store_true',
                       help='Display current configuration and exit')
    
    args = parser.parse_args()
    
    try:
        # Initialize manager
        manager = AzureTestPointManager()
        
        # Handle configuration display
        if args.show_config:
            print("🔧 Current Configuration:")
            print(f"   Organization: {manager.organization_url}")
            print(f"   Project: {manager.project_name}")
            print(f"   PAT: {'✅ Set' if manager.personal_access_token else '❌ Not Set'}")
            if manager.personal_access_token:
                token = manager.personal_access_token
                print(f"   PAT Preview: {token[:10]}...{token[-4:]} (length: {len(token)})")
            return 0
        
        # Validate that plan_id is provided for operations that need it
        if not args.plan_id:
            print("❌ Error: plan_id is required for test point operations")
            print("Usage examples:")
            print("  azure-devops-test-manager 679333              # List test points")
            print("  azure-devops-test-manager --show-config       # Show configuration")
            print("  azure-devops-test-manager --help              # Show all options")
            return 1
        
        print(f"🔗 Connected to: {manager.organization_url}")
        print(f"📋 Project: {manager.project_name}")
        
        # Check if this is an XML-based update operation
        if args.from_xml:
            print(f"\n{'='*80}")
            print(f"{'DRY RUN - ' if args.dry_run else ''}UPDATING FROM TEST RESULTS")
            print(f"{'='*80}")
            print(f"Plan ID: {args.plan_id}")
            print(f"XML File: {args.from_xml}")
            print(f"Suite ID: {args.suite_id if args.suite_id else 'All suites'}")
            print(f"Min Score: {args.min_score}")
            print(f"{'='*80}")
            
            if not args.dry_run:
                # Update test points based on XML test results
                update_results = manager.update_from_test_results(
                    plan_id=args.plan_id,
                    xml_file_path=args.from_xml,
                    suite_id=args.suite_id,
                    min_score=args.min_score,
                    comment=args.comment
                )
                
                if 'error' in update_results:
                    print(f"\n❌ Update failed: {update_results['error']}")
                    return 1
                
                print(f"\n✅ XML-based update completed! {update_results['total_updated']}/{update_results['total_matches']} points updated.")
            else:
                print("\n🔍 Dry run mode - no actual updates will be performed.")
                # You could add dry-run preview logic here
                print("Use without --dry-run to perform actual updates.")
            
            return 0
        
        # Check if this is a manual update operation
        elif args.update_outcome:
            # Build filter criteria
            filter_criteria = {}
            if args.filter_outcome:
                filter_criteria['current_outcome'] = args.filter_outcome
            if args.filter_automated is not None:
                filter_criteria['automated'] = args.filter_automated
            if args.filter_state:
                filter_criteria['state'] = args.filter_state
            if args.filter_name:
                filter_criteria['test_name_contains'] = args.filter_name
            
            # Perform update operation
            update_results = update_points_by_criteria(
                manager=manager,
                plan_id=args.plan_id,
                suite_id=args.suite_id,
                outcome=args.update_outcome,
                filter_criteria=filter_criteria if filter_criteria else None,
                dry_run=args.dry_run,
                comment=args.comment
            )
            
            if args.dry_run:
                print(f"\n🔍 Dry run completed. {update_results['total_eligible']} points would be updated.")
            else:
                print(f"\n✅ Update completed! {update_results['total_updated']}/{update_results['total_eligible']} points updated.")
            
            return 0 if update_results['total_updated'] >= 0 else 1
        
        else:
            # Regular listing operation
            print(f"\n{'='*80}")
            print(f"Azure DevOps Test Points Lister")
            print(f"{'='*80}")
            print(f"Organization: {manager.organization_url}")
            print(f"Project: {manager.project_name}")
            print(f"Test Plan ID: {args.plan_id}")
            print(f"Suite ID: {args.suite_id if args.suite_id else 'All suites'}")
            print(f"Detailed Mode: {'Yes' if args.detailed else 'No'}")
            print(f"{'='*80}")
            
            results = manager.list_test_points_for_plan(
                plan_id=args.plan_id,
                suite_id=args.suite_id,
                detailed=args.detailed
            )
            
            if not results:
                print("No test points found or error occurred.")
                return 1
            
            # Output results
            if args.output == 'console':
                print_console_output(results, args.detailed)
            elif args.output == 'json':
                save_json_output(results, args.plan_id)
            elif args.output == 'csv':
                save_csv_output(results, args.plan_id)
            
            print(f"\n✅ Successfully processed test points!")
            return 0
    
    except ConfigurationError as e:
        print(f"❌ Configuration Error: {e}")
        print("\nPlease set the required environment variables:")
        print("export AZURE_DEVOPS_PAT='your_token_here'")
        print("export AZURE_DEVOPS_ORG='https://dev.azure.com/yourorg'")
        print("export AZURE_DEVOPS_PROJECT='Your Project Name'")
        return 1
    
    except AzureAPIError as e:
        print(f"❌ Azure API Error: {e}")
        return 1
    
    except FileNotFoundError as e:
        print(f"❌ File Error: {e}")
        return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        return 1
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())