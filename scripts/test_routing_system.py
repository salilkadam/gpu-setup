#!/usr/bin/env python3
"""
Test Script for Intelligent Model Routing System

This script tests the complete routing system including:
- Query classification
- Model routing
- Dynamic loading
- API endpoints
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Any
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from routing.query_classifier import QueryClassifier, UseCase
from routing.model_router import ModelRouter
from routing.dynamic_loader import DynamicModelLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
ROUTING_API_URL = "http://localhost:8001"
VLLM_API_URL = "http://localhost:8000"
TEST_QUERIES = [
    {
        "query": "Write a Python function to sort a list",
        "expected_use_case": "agent",
        "description": "Code generation query"
    },
    {
        "query": "Generate a talking head avatar with lip sync",
        "expected_use_case": "avatar",
        "description": "Avatar generation query"
    },
    {
        "query": "Transcribe this audio file to text",
        "expected_use_case": "stt",
        "description": "Speech-to-text query"
    },
    {
        "query": "Convert this text to speech in Hindi",
        "expected_use_case": "tts",
        "description": "Text-to-speech query"
    },
    {
        "query": "Analyze this image and describe what you see",
        "expected_use_case": "multimodal",
        "description": "Multimodal analysis query"
    },
    {
        "query": "Process this video and extract key frames",
        "expected_use_case": "video",
        "description": "Video processing query"
    }
]


class RoutingSystemTester:
    """Test the intelligent model routing system."""
    
    def __init__(self):
        self.classifier = QueryClassifier()
        self.router = ModelRouter()
        self.loader = DynamicModelLoader()
        self.session = None
        self.test_results = []
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def test_query_classification(self) -> Dict[str, Any]:
        """Test query classification functionality."""
        logger.info("Testing query classification...")
        
        results = {
            "test_name": "Query Classification",
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        for test_case in TEST_QUERIES:
            try:
                classification = await self.classifier.classify_query(test_case["query"])
                
                success = classification.use_case.value == test_case["expected_use_case"]
                
                if success:
                    results["passed"] += 1
                    logger.info(f"✅ {test_case['description']}: {classification.use_case.value}")
                else:
                    results["failed"] += 1
                    logger.error(f"❌ {test_case['description']}: Expected {test_case['expected_use_case']}, got {classification.use_case.value}")
                
                results["details"].append({
                    "query": test_case["query"],
                    "expected": test_case["expected_use_case"],
                    "actual": classification.use_case.value,
                    "confidence": classification.confidence,
                    "success": success
                })
                
            except Exception as e:
                results["failed"] += 1
                logger.error(f"❌ Error testing {test_case['description']}: {e}")
                results["details"].append({
                    "query": test_case["query"],
                    "error": str(e),
                    "success": False
                })
        
        return results
    
    async def test_model_routing(self) -> Dict[str, Any]:
        """Test model routing functionality."""
        logger.info("Testing model routing...")
        
        results = {
            "test_name": "Model Routing",
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        for test_case in TEST_QUERIES:
            try:
                # Classify query
                classification = await self.classifier.classify_query(test_case["query"])
                
                # Route to model
                routing_decision = await self.router.route_query(classification)
                
                success = routing_decision.selected_model is not None
                
                if success:
                    results["passed"] += 1
                    logger.info(f"✅ {test_case['description']}: Routed to {routing_decision.selected_model.model_id}")
                else:
                    results["failed"] += 1
                    logger.error(f"❌ {test_case['description']}: No model selected")
                
                results["details"].append({
                    "query": test_case["query"],
                    "selected_model": routing_decision.selected_model.model_id if routing_decision.selected_model else None,
                    "confidence": routing_decision.confidence,
                    "reasoning": routing_decision.reasoning,
                    "success": success
                })
                
            except Exception as e:
                results["failed"] += 1
                logger.error(f"❌ Error routing {test_case['description']}: {e}")
                results["details"].append({
                    "query": test_case["query"],
                    "error": str(e),
                    "success": False
                })
        
        return results
    
    async def test_api_endpoints(self) -> Dict[str, Any]:
        """Test API endpoints."""
        logger.info("Testing API endpoints...")
        
        results = {
            "test_name": "API Endpoints",
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        # Test health endpoint
        try:
            async with self.session.get(f"{ROUTING_API_URL}/health") as response:
                if response.status == 200:
                    results["passed"] += 1
                    logger.info("✅ Health endpoint working")
                else:
                    results["failed"] += 1
                    logger.error(f"❌ Health endpoint failed: {response.status}")
                
                results["details"].append({
                    "endpoint": "/health",
                    "status": response.status,
                    "success": response.status == 200
                })
        except Exception as e:
            results["failed"] += 1
            logger.error(f"❌ Health endpoint error: {e}")
            results["details"].append({
                "endpoint": "/health",
                "error": str(e),
                "success": False
            })
        
        # Test use cases endpoint
        try:
            async with self.session.get(f"{ROUTING_API_URL}/use-cases") as response:
                if response.status == 200:
                    data = await response.json()
                    if "use_cases" in data and len(data["use_cases"]) > 0:
                        results["passed"] += 1
                        logger.info("✅ Use cases endpoint working")
                    else:
                        results["failed"] += 1
                        logger.error("❌ Use cases endpoint returned no data")
                else:
                    results["failed"] += 1
                    logger.error(f"❌ Use cases endpoint failed: {response.status}")
                
                results["details"].append({
                    "endpoint": "/use-cases",
                    "status": response.status,
                    "success": response.status == 200
                })
        except Exception as e:
            results["failed"] += 1
            logger.error(f"❌ Use cases endpoint error: {e}")
            results["details"].append({
                "endpoint": "/use-cases",
                "error": str(e),
                "success": False
            })
        
        # Test routing endpoint
        try:
            test_query = {
                "query": "Write a Python function to sort a list",
                "modality": "text"
            }
            
            async with self.session.post(f"{ROUTING_API_URL}/route", json=test_query) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success") and data.get("result"):
                        results["passed"] += 1
                        logger.info("✅ Routing endpoint working")
                    else:
                        results["failed"] += 1
                        logger.error("❌ Routing endpoint returned no result")
                else:
                    results["failed"] += 1
                    logger.error(f"❌ Routing endpoint failed: {response.status}")
                
                results["details"].append({
                    "endpoint": "/route",
                    "status": response.status,
                    "success": response.status == 200
                })
        except Exception as e:
            results["failed"] += 1
            logger.error(f"❌ Routing endpoint error: {e}")
            results["details"].append({
                "endpoint": "/route",
                "error": str(e),
                "success": False
            })
        
        return results
    
    async def test_vllm_integration(self) -> Dict[str, Any]:
        """Test vLLM integration."""
        logger.info("Testing vLLM integration...")
        
        results = {
            "test_name": "vLLM Integration",
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        # Test vLLM health
        try:
            async with self.session.get(f"{VLLM_API_URL}/health") as response:
                if response.status == 200:
                    results["passed"] += 1
                    logger.info("✅ vLLM health check passed")
                else:
                    results["failed"] += 1
                    logger.error(f"❌ vLLM health check failed: {response.status}")
                
                results["details"].append({
                    "test": "vLLM Health",
                    "status": response.status,
                    "success": response.status == 200
                })
        except Exception as e:
            results["failed"] += 1
            logger.error(f"❌ vLLM health check error: {e}")
            results["details"].append({
                "test": "vLLM Health",
                "error": str(e),
                "success": False
            })
        
        # Test vLLM models endpoint
        try:
            async with self.session.get(f"{VLLM_API_URL}/v1/models") as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data and len(data["data"]) > 0:
                        results["passed"] += 1
                        logger.info("✅ vLLM models endpoint working")
                    else:
                        results["failed"] += 1
                        logger.error("❌ vLLM models endpoint returned no models")
                else:
                    results["failed"] += 1
                    logger.error(f"❌ vLLM models endpoint failed: {response.status}")
                
                results["details"].append({
                    "test": "vLLM Models",
                    "status": response.status,
                    "success": response.status == 200
                })
        except Exception as e:
            results["failed"] += 1
            logger.error(f"❌ vLLM models endpoint error: {e}")
            results["details"].append({
                "test": "vLLM Models",
                "error": str(e),
                "success": False
            })
        
        return results
    
    async def test_system_status(self) -> Dict[str, Any]:
        """Test system status endpoint."""
        logger.info("Testing system status...")
        
        results = {
            "test_name": "System Status",
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        try:
            async with self.session.get(f"{ROUTING_API_URL}/status") as response:
                if response.status == 200:
                    data = await response.json()
                    if "status" in data and "loaded_models" in data:
                        results["passed"] += 1
                        logger.info("✅ System status endpoint working")
                        logger.info(f"   Status: {data['status']}")
                        logger.info(f"   Loaded models: {data['loaded_models']}")
                    else:
                        results["failed"] += 1
                        logger.error("❌ System status endpoint returned incomplete data")
                else:
                    results["failed"] += 1
                    logger.error(f"❌ System status endpoint failed: {response.status}")
                
                results["details"].append({
                    "test": "System Status",
                    "status": response.status,
                    "success": response.status == 200
                })
        except Exception as e:
            results["failed"] += 1
            logger.error(f"❌ System status endpoint error: {e}")
            results["details"].append({
                "test": "System Status",
                "error": str(e),
                "success": False
            })
        
        return results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        logger.info("Starting comprehensive routing system tests...")
        
        start_time = time.time()
        
        # Run all test suites
        test_suites = [
            self.test_query_classification(),
            self.test_model_routing(),
            self.test_api_endpoints(),
            self.test_vllm_integration(),
            self.test_system_status()
        ]
        
        results = await asyncio.gather(*test_suites, return_exceptions=True)
        
        # Process results
        total_passed = 0
        total_failed = 0
        test_summary = []
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Test suite failed with exception: {result}")
                total_failed += 1
                test_summary.append({
                    "test_name": "Unknown",
                    "passed": 0,
                    "failed": 1,
                    "error": str(result)
                })
            else:
                total_passed += result["passed"]
                total_failed += result["failed"]
                test_summary.append(result)
        
        total_time = time.time() - start_time
        
        return {
            "summary": {
                "total_tests": len(test_suites),
                "total_passed": total_passed,
                "total_failed": total_failed,
                "success_rate": (total_passed / (total_passed + total_failed)) * 100 if (total_passed + total_failed) > 0 else 0,
                "total_time": total_time
            },
            "test_results": test_summary
        }
    
    def print_results(self, results: Dict[str, Any]):
        """Print test results in a formatted way."""
        print("\n" + "="*80)
        print("INTELLIGENT MODEL ROUTING SYSTEM - TEST RESULTS")
        print("="*80)
        
        summary = results["summary"]
        print(f"\n📊 SUMMARY:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['total_passed']}")
        print(f"   Failed: {summary['total_failed']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Total Time: {summary['total_time']:.2f}s")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_result in results["test_results"]:
            print(f"\n   {test_result['test_name']}:")
            print(f"     Passed: {test_result['passed']}")
            print(f"     Failed: {test_result['failed']}")
            
            if "error" in test_result:
                print(f"     Error: {test_result['error']}")
        
        print("\n" + "="*80)
        
        if summary['total_failed'] == 0:
            print("🎉 ALL TESTS PASSED! The routing system is working correctly.")
        else:
            print(f"⚠️  {summary['total_failed']} tests failed. Please check the logs for details.")
        
        print("="*80)


async def main():
    """Main test function."""
    print("🚀 Starting Intelligent Model Routing System Tests...")
    
    async with RoutingSystemTester() as tester:
        results = await tester.run_all_tests()
        tester.print_results(results)
        
        # Save results to file
        with open("routing_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: routing_test_results.json")
        
        # Return exit code based on results
        if results["summary"]["total_failed"] == 0:
            return 0
        else:
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
