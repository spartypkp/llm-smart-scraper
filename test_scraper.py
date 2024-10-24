from scraper import LegislationScraper, ScraperResult
from pathfinder import Pathfinder, PathfinderResult
from typing import List, Dict
import json
import logging
from datetime import datetime
from pydanticModels import Citation
import database as db
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'scraper_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_test_citations() -> List[Citation]:
    """
    Placeholder for database function to get citations
    You'll implement the actual database connection
    """
    test_id = "14489ro9de72fd7145c7b640619c71766673435"
    hashtagged_citation = db.pydantic_select(f"SELECT * FROM citations WHERE id='{test_id}';", Citation)
    return hashtagged_citation

def test_single_citation(scraper: LegislationScraper, citation: Citation) -> Dict:
    """Test scraper on a single citation and return results"""
    logger.info(f"Testing citation: {citation.id}")
    logger.info(f"Legal reference: {citation.legal_reference}")
    
    try:
        result = scraper.get_legislation_content(citation)
        
        test_result = {
            'citation_id': citation.id,
            'legal_reference': citation.legal_reference,
            'url': citation.link_legal_reference,
            'processing_path': result.processing_path,
            'status': result.status,
            'confidence': result.confidence,
            'requires_human_review': result.requires_human_review,
            'error_message': result.error_message,
            'content_length': len(result.content) if result.content else 0,
            'has_content': bool(result.content)
        }
        
        logger.info(f"Test completed for {citation.id}: {result.status}")
        return test_result
        
    except Exception as e:
        logger.error(f"Error testing citation {citation.id}: {str(e)}")
        return {
            'citation_id': citation.id,
            'status': 'error',
            'error_message': str(e)
        }

def run_batch_test(citations: List[Citation], sample_size: int = None) -> None:
    """Run tests on a batch of citations"""
    scraper = LegislationScraper()
    results = []
    
    # Take a sample if specified
    test_citations = citations[:sample_size] if sample_size else citations
    
    logger.info(f"Starting batch test with {len(test_citations)} citations")
    
    for citation in test_citations:
        results.append(test_single_citation(scraper, citation))
    
    # Save results
    save_test_results(results)
    
    # Print summary
    print_test_summary(results)

def save_test_results(results: List[Dict]) -> None:
    """Save test results to a file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'scraper_results_{timestamp}.json'
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {filename}")

def print_test_summary(results: List[Dict]) -> None:
    """Print summary statistics of test results"""
    total = len(results)
    successful = sum(1 for r in results if r['status'] == 'success')
    needs_review = sum(1 for r in results if r['requires_human_review'])
    errors = sum(1 for r in results if r['status'] == 'error')
    
    path_counts = {}
    for r in results:
        path = r.get('processing_path', 'unknown')
        path_counts[path] = path_counts.get(path, 0) + 1
    
    print("\n=== Test Summary ===")
    print(f"Total citations tested: {total}")
    print(f"Successful extractions: {successful} ({(successful/total)*100:.1f}%)")
    print(f"Needs human review: {needs_review} ({(needs_review/total)*100:.1f}%)")
    print(f"Errors: {errors} ({(errors/total)*100:.1f}%)")
    print("\nProcessing Paths:")
    for path, count in path_counts.items():
        print(f"  {path}: {count} ({(count/total)*100:.1f}%)")

def test_specific_citations(citation_ids: List[str]) -> None:
    """Test specific citations by their IDs"""
    # You'll implement the database query to get these specific citations
    citations = get_test_citations_by_ids(citation_ids)
    run_batch_test(citations)

def get_test_citations_by_ids(citation_ids: List[str]) -> List[Citation]:
    """
    Placeholder for database function to get specific citations
    You'll implement the actual database query
    """
    pass

if __name__ == "__main__":
    # Example usage:
    
    # Test all citations (or a sample)
    citations = get_test_citations()
    result = test_single_citation(LegislationScraper(headless=False), citations[0])
    print(result)
    #run_batch_test(citations, sample_size=10)  # Test 10 citations
    
    # # Test specific citations
    # test_specific_citations([
    #     "citation_id_1",
    #     "citation_id_2",
    #     # Add more citation IDs as needed
    # ])
    
    # # Test citations from specific jurisdictions or with specific patterns
    # citations = get_test_citations()
    # specific_citations = [c for c in citations if '#' in c.link_legal_reference]
    # run_batch_test(specific_citations)