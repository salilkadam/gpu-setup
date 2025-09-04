#!/usr/bin/env python3
"""
Test Script for Smart Bypass Optimization

This script demonstrates the smart bypass optimization for real-time conversations,
showing the dramatic latency improvements achieved.
"""

import asyncio
import aiohttp
import time
import json
import logging
from typing import List, Dict, Any
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
REALTIME_API_URL = "http://localhost:8001"
TEST_CONVERSATIONS = [
    {
        "name": "Python Programming Session",
        "queries": [
            "Write a Python function to sort a list",
            "Can you add error handling to that function?",
            "What about adding type hints?",
            "Make it more efficient with a different algorithm",
            "Now write a test for this function",
            "Add documentation to the function",
            "Create a class that uses this function"
        ]
    },
    {
        "name": "Avatar Generation Session", 
        "queries": [
            "Generate a talking head avatar with lip sync",
            "Make the avatar speak the text I provide",
            "Add facial expressions to the avatar",
            "Change the avatar's voice to be more energetic",
            "Add background music to the avatar video"
        ]
    },
    {
        "name": "Mixed Modality Session",
        "queries": [
            "Write a Python script to process images",
            "Now analyze this image and describe what you see",
            "Generate code to extract text from the image",
            "Create a function to resize the image",
            "Add error handling for invalid image formats"
        ]
    }
]


class SmartBypassTester:
    """Test the smart bypass optimization."""
    
    def __init__(self):
        self.session = None
        self.results = []
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def test_conversation(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Test a complete conversation with smart bypass."""
        logger.info(f"🚀 Testing: {conversation['name']}")
        
        conversation_results = {
            "name": conversation["name"],
            "queries": [],
            "session_id": None,
            "total_time": 0.0,
            "routing_times": [],
            "bypass_usage": [],
            "performance_summary": {}
        }
        
        start_time = time.time()
        
        for i, query in enumerate(conversation["queries"]):
            query_start = time.time()
            
            try:
                # Make request to real-time API
                request_data = {
                    "query": query,
                    "session_id": conversation_results["session_id"],
                    "max_tokens": 100,
                    "temperature": 0.7
                }
                
                async with self.session.post(
                    f"{REALTIME_API_URL}/route",
                    json=request_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Store session ID from first request
                        if not conversation_results["session_id"]:
                            conversation_results["session_id"] = result.get("session_id")
                        
                        query_time = time.time() - query_start
                        
                        query_result = {
                            "query": query,
                            "query_number": i + 1,
                            "use_case": result.get("use_case"),
                            "selected_model": result.get("selected_model"),
                            "confidence": result.get("confidence"),
                            "routing_time": result.get("routing_time", 0) * 1000,  # Convert to ms
                            "bypass_used": result.get("bypass_used", False),
                            "new_session": result.get("new_session", False),
                            "inference_time": result.get("inference_time", 0) * 1000,  # Convert to ms
                            "total_time": result.get("total_time", 0) * 1000,  # Convert to ms
                            "query_time": query_time * 1000  # Convert to ms
                        }
                        
                        conversation_results["queries"].append(query_result)
                        conversation_results["routing_times"].append(query_result["routing_time"])
                        conversation_results["bypass_usage"].append(query_result["bypass_used"])
                        
                        logger.info(f"  Query {i+1}: {query[:50]}...")
                        logger.info(f"    Use Case: {query_result['use_case']}")
                        logger.info(f"    Bypass Used: {'✅' if query_result['bypass_used'] else '❌'}")
                        logger.info(f"    Routing Time: {query_result['routing_time']:.1f}ms")
                        logger.info(f"    Total Time: {query_result['total_time']:.1f}ms")
                        
                    else:
                        error_text = await response.text()
                        logger.error(f"  Query {i+1} failed: {response.status} - {error_text}")
                        
                        query_result = {
                            "query": query,
                            "query_number": i + 1,
                            "error": f"HTTP {response.status}: {error_text}",
                            "routing_time": 0,
                            "bypass_used": False,
                            "total_time": 0
                        }
                        
                        conversation_results["queries"].append(query_result)
                        
            except Exception as e:
                logger.error(f"  Query {i+1} error: {e}")
                
                query_result = {
                    "query": query,
                    "query_number": i + 1,
                    "error": str(e),
                    "routing_time": 0,
                    "bypass_used": False,
                    "total_time": 0
                }
                
                conversation_results["queries"].append(query_result)
        
        conversation_results["total_time"] = time.time() - start_time
        
        # Calculate performance summary
        conversation_results["performance_summary"] = self._calculate_performance_summary(
            conversation_results
        )
        
        return conversation_results
    
    def _calculate_performance_summary(self, conversation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance summary for a conversation."""
        queries = conversation_results["queries"]
        routing_times = conversation_results["routing_times"]
        bypass_usage = conversation_results["bypass_usage"]
        
        if not queries:
            return {}
        
        # Calculate statistics
        total_queries = len(queries)
        bypass_count = sum(bypass_usage)
        bypass_rate = (bypass_count / total_queries) * 100 if total_queries > 0 else 0
        
        # Calculate timing statistics
        valid_routing_times = [t for t in routing_times if t > 0]
        valid_total_times = [q["total_time"] for q in queries if q["total_time"] > 0]
        
        avg_routing_time = sum(valid_routing_times) / len(valid_routing_times) if valid_routing_times else 0
        avg_total_time = sum(valid_total_times) / len(valid_total_times) if valid_total_times else 0
        min_routing_time = min(valid_routing_times) if valid_routing_times else 0
        max_routing_time = max(valid_routing_times) if valid_routing_times else 0
        
        return {
            "total_queries": total_queries,
            "bypass_count": bypass_count,
            "bypass_rate_percent": bypass_rate,
            "avg_routing_time_ms": avg_routing_time,
            "avg_total_time_ms": avg_total_time,
            "min_routing_time_ms": min_routing_time,
            "max_routing_time_ms": max_routing_time,
            "conversation_duration_s": conversation_results["total_time"]
        }
    
    async def test_api_health(self) -> bool:
        """Test API health."""
        try:
            async with self.session.get(f"{REALTIME_API_URL}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info("✅ API Health Check Passed")
                    logger.info(f"   Status: {health_data.get('status')}")
                    return True
                else:
                    logger.error(f"❌ API Health Check Failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ API Health Check Error: {e}")
            return False
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get overall performance statistics."""
        try:
            async with self.session.get(f"{REALTIME_API_URL}/stats") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get performance stats: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return {}
    
    def print_conversation_results(self, results: Dict[str, Any]):
        """Print conversation results in a formatted way."""
        print(f"\n📊 CONVERSATION RESULTS: {results['name']}")
        print("=" * 60)
        
        summary = results["performance_summary"]
        print(f"Total Queries: {summary.get('total_queries', 0)}")
        print(f"Bypass Rate: {summary.get('bypass_rate_percent', 0):.1f}%")
        print(f"Average Routing Time: {summary.get('avg_routing_time_ms', 0):.1f}ms")
        print(f"Average Total Time: {summary.get('avg_total_time_ms', 0):.1f}ms")
        print(f"Min Routing Time: {summary.get('min_routing_time_ms', 0):.1f}ms")
        print(f"Max Routing Time: {summary.get('max_routing_time_ms', 0):.1f}ms")
        print(f"Conversation Duration: {summary.get('conversation_duration_s', 0):.2f}s")
        
        print(f"\n📋 QUERY BREAKDOWN:")
        for query_result in results["queries"]:
            status = "✅" if not query_result.get("error") else "❌"
            bypass = "🚀" if query_result.get("bypass_used") else "🔄"
            print(f"  {status} {bypass} Q{query_result['query_number']}: {query_result['routing_time']:.1f}ms")
    
    def print_overall_summary(self, all_results: List[Dict[str, Any]], api_stats: Dict[str, Any]):
        """Print overall test summary."""
        print("\n" + "="*80)
        print("🎯 SMART BYPASS OPTIMIZATION - TEST SUMMARY")
        print("="*80)
        
        # Calculate overall statistics
        total_queries = sum(r["performance_summary"].get("total_queries", 0) for r in all_results)
        total_bypass = sum(r["performance_summary"].get("bypass_count", 0) for r in all_results)
        overall_bypass_rate = (total_bypass / total_queries * 100) if total_queries > 0 else 0
        
        avg_routing_times = [r["performance_summary"].get("avg_routing_time_ms", 0) for r in all_results if r["performance_summary"].get("avg_routing_time_ms", 0) > 0]
        overall_avg_routing = sum(avg_routing_times) / len(avg_routing_times) if avg_routing_times else 0
        
        avg_total_times = [r["performance_summary"].get("avg_total_time_ms", 0) for r in all_results if r["performance_summary"].get("avg_total_time_ms", 0) > 0]
        overall_avg_total = sum(avg_total_times) / len(avg_total_times) if avg_total_times else 0
        
        print(f"\n📊 OVERALL PERFORMANCE:")
        print(f"   Total Conversations: {len(all_results)}")
        print(f"   Total Queries: {total_queries}")
        print(f"   Overall Bypass Rate: {overall_bypass_rate:.1f}%")
        print(f"   Average Routing Time: {overall_avg_routing:.1f}ms")
        print(f"   Average Total Time: {overall_avg_total:.1f}ms")
        
        if api_stats:
            print(f"\n🔧 API STATISTICS:")
            print(f"   Total API Requests: {api_stats.get('total_requests', 0)}")
            print(f"   API Bypass Rate: {api_stats.get('bypass_rate_percent', 0):.1f}%")
            print(f"   API Avg Routing Time: {api_stats.get('average_routing_time', 0)*1000:.1f}ms")
            print(f"   API Avg Bypass Time: {api_stats.get('average_bypass_time', 0)*1000:.1f}ms")
        
        print(f"\n🎯 LATENCY IMPROVEMENTS:")
        print(f"   Original System: 2,300-5,600ms (first request)")
        print(f"   Smart Bypass: {overall_avg_total:.0f}ms (average)")
        improvement = ((2300 - overall_avg_total) / 2300) * 100
        print(f"   Improvement: {improvement:.1f}% faster")
        
        print(f"\n🚀 REAL-TIME READINESS:")
        if overall_avg_total < 300:
            print("   ✅ EXCELLENT: Ready for real-time conversations")
        elif overall_avg_total < 500:
            print("   ✅ GOOD: Suitable for real-time conversations")
        elif overall_avg_total < 1000:
            print("   ⚠️  ACCEPTABLE: May have slight delays")
        else:
            print("   ❌ POOR: Not suitable for real-time conversations")
        
        print("="*80)


async def main():
    """Main test function."""
    print("🚀 Starting Smart Bypass Optimization Tests...")
    print("=" * 60)
    
    async with SmartBypassTester() as tester:
        # Test API health
        health_ok = await tester.test_api_health()
        if not health_ok:
            print("❌ API health check failed. Please ensure the real-time API is running.")
            return 1
        
        # Test all conversations
        all_results = []
        for conversation in TEST_CONVERSATIONS:
            results = await tester.test_conversation(conversation)
            all_results.append(results)
            tester.print_conversation_results(results)
        
        # Get API performance stats
        api_stats = await tester.get_performance_stats()
        
        # Print overall summary
        tester.print_overall_summary(all_results, api_stats)
        
        # Save results to file
        with open("smart_bypass_test_results.json", "w") as f:
            json.dump({
                "conversations": all_results,
                "api_stats": api_stats,
                "timestamp": time.time()
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: smart_bypass_test_results.json")
        
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
