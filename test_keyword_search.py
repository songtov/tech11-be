#!/usr/bin/env python3
"""
Test script for keyword search functionality
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.research import ResearchService
from app.core.database import get_db

def test_keyword_search():
    """Test the keyword search functionality"""
    
    # Create a mock database session (we'll use None for testing)
    db_session = None
    
    # Create the service
    service = ResearchService(db_session)
    
    # Test with a simple keyword
    test_keyword = "machine learning"
    
    print(f"Testing keyword search with: '{test_keyword}'")
    print("=" * 50)
    
    try:
        # Test direct arXiv search
        print("1. Testing direct arXiv search...")
        direct_papers = service._search_arxiv_with_query(test_keyword, max_results=5)
        print(f"   Direct search found {len(direct_papers)} papers")
        
        if direct_papers:
            for i, paper in enumerate(direct_papers[:3], 1):
                print(f"   Paper {i}: {paper.title[:60]}...")
        
        print("\n2. Testing title search...")
        title_papers = service._search_arxiv_with_query(f"ti:{test_keyword}", max_results=5)
        print(f"   Title search found {len(title_papers)} papers")
        
        if title_papers:
            for i, paper in enumerate(title_papers[:3], 1):
                print(f"   Paper {i}: {paper.title[:60]}...")
        
        print("\n3. Testing full keyword search...")
        result = service.search_research_by_keyword(test_keyword)
        print(f"   Full search returned {len(result.data)} results")
        
        for i, paper in enumerate(result.data[:3], 1):
            print(f"   Result {i}: {paper.title[:60]}...")
            
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_keyword_search()
