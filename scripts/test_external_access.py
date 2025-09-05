#!/usr/bin/env python3
"""
External Access Testing Script

This script tests the AI infrastructure endpoints from external machines
to verify that the Kubernetes ingress and networking is working correctly.
"""

import requests
import json
import time
import os
from typing import Dict, Any, Optional

class ExternalAccessTester:
    """Test external access to AI infrastructure endpoints."""
    
    def __init__(self, base_domain: str = "yourdomain.com", use_https: bool = True):
        self.base_domain = base_domain
        self.protocol = "https" if use_https else "http"
        self.test_results = {}
        
        # External endpoints
        self.endpoints = {
            "main_api": f"{self.protocol}://ai-api.{base_domain}",
            "stt_service": f"{self.protocol}://ai-stt.{base_domain}",
            "tts_service": f"{self.protocol}://ai-tts.{base_domain}",
            "vllm_service": f"{self.protocol}://ai-vllm.{base_domain}",
            "single_domain": f"{self.protocol}://ai.{base_domain}"
        }
        
        # Internal endpoints (for comparison)
        self.internal_endpoints = {
            "main_api": "http://ai-api.internal",
            "stt_service": "http://ai-stt.internal",
            "tts_service": "http://ai-tts.internal",
            "vllm_service": "http://ai-vllm.internal"
        }
    
    def test_endpoint_connectivity(self, url: str, name: str) -> Dict[str, Any]:
        """Test basic connectivity to an endpoint."""
        print(f"🔍 Testing {name}: {url}")
        
        try:
            # Test basic connectivity
            response = requests.get(f"{url}/health", timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ {name} is accessible")
                return {
                    "name": name,
                    "url": url,
                    "accessible": True,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "health_data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                }
            else:
                print(f"   ❌ {name} returned status {response.status_code}")
                return {
                    "name": name,
                    "url": url,
                    "accessible": False,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}"
                }
        except requests.exceptions.Timeout:
            print(f"   ⏰ {name} timed out")
            return {
                "name": name,
                "url": url,
                "accessible": False,
                "error": "Timeout"
            }
        except requests.exceptions.ConnectionError:
            print(f"   🔌 {name} connection failed")
            return {
                "name": name,
                "url": url,
                "accessible": False,
                "error": "Connection failed"
            }
        except Exception as e:
            print(f"   ❌ {name} error: {e}")
            return {
                "name": name,
                "url": url,
                "accessible": False,
                "error": str(e)
            }
    
    def test_routing_api(self) -> Dict[str, Any]:
        """Test the main routing API."""
        print("\n🚀 Testing Main Routing API")
        print("=" * 50)
        
        results = []
        
        # Test external endpoint
        external_result = self.test_endpoint_connectivity(
            self.endpoints["main_api"], 
            "External Routing API"
        )
        results.append(external_result)
        
        # Test single domain endpoint
        single_domain_result = self.test_endpoint_connectivity(
            f"{self.endpoints['single_domain']}/api", 
            "Single Domain Routing API"
        )
        results.append(single_domain_result)
        
        # Test internal endpoint (if accessible)
        try:
            internal_result = self.test_endpoint_connectivity(
                self.internal_endpoints["main_api"], 
                "Internal Routing API"
            )
            results.append(internal_result)
        except:
            print("   ⚠️ Internal endpoint not accessible from external machine")
        
        # Test API functionality
        if external_result.get("accessible"):
            print("\n🔍 Testing API functionality...")
            try:
                response = requests.post(
                    f"{self.endpoints['main_api']}/route",
                    json={
                        "query": "Hello, world!",
                        "modality": "text"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ API functionality test passed")
                    print(f"   Use Case: {result.get('use_case')}")
                    print(f"   Response Time: {result.get('total_time', 0):.3f}s")
                    
                    results.append({
                        "name": "API Functionality Test",
                        "accessible": True,
                        "use_case": result.get('use_case'),
                        "response_time": result.get('total_time'),
                        "confidence": result.get('confidence')
                    })
                else:
                    print(f"   ❌ API functionality test failed: {response.status_code}")
                    results.append({
                        "name": "API Functionality Test",
                        "accessible": False,
                        "error": f"HTTP {response.status_code}"
                    })
            except Exception as e:
                print(f"   ❌ API functionality test error: {e}")
                results.append({
                    "name": "API Functionality Test",
                    "accessible": False,
                    "error": str(e)
                })
        
        return {"routing_api_tests": results}
    
    def test_audio_services(self) -> Dict[str, Any]:
        """Test STT and TTS services."""
        print("\n🎤 Testing Audio Services")
        print("=" * 50)
        
        results = []
        
        # Test STT service
        print("\n🔍 Testing STT Service")
        stt_result = self.test_endpoint_connectivity(
            self.endpoints["stt_service"], 
            "External STT Service"
        )
        results.append(stt_result)
        
        # Test STT single domain
        stt_single_result = self.test_endpoint_connectivity(
            f"{self.endpoints['single_domain']}/stt", 
            "Single Domain STT Service"
        )
        results.append(stt_single_result)
        
        # Test TTS service
        print("\n🔍 Testing TTS Service")
        tts_result = self.test_endpoint_connectivity(
            self.endpoints["tts_service"], 
            "External TTS Service"
        )
        results.append(tts_result)
        
        # Test TTS single domain
        tts_single_result = self.test_endpoint_connectivity(
            f"{self.endpoints['single_domain']}/tts", 
            "Single Domain TTS Service"
        )
        results.append(tts_single_result)
        
        # Test TTS functionality
        if tts_result.get("accessible"):
            print("\n🔍 Testing TTS functionality...")
            try:
                response = requests.post(
                    f"{self.endpoints['tts_service']}/synthesize",
                    json={
                        "text": "Hello, this is a test.",
                        "language": "hi",
                        "gender": "female"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ TTS functionality test passed")
                    print(f"   Language: {result.get('language')}")
                    print(f"   Gender: {result.get('gender')}")
                    print(f"   Duration: {result.get('duration', 0):.2f}s")
                    
                    results.append({
                        "name": "TTS Functionality Test",
                        "accessible": True,
                        "language": result.get('language'),
                        "gender": result.get('gender'),
                        "duration": result.get('duration')
                    })
                else:
                    print(f"   ❌ TTS functionality test failed: {response.status_code}")
                    results.append({
                        "name": "TTS Functionality Test",
                        "accessible": False,
                        "error": f"HTTP {response.status_code}"
                    })
            except Exception as e:
                print(f"   ❌ TTS functionality test error: {e}")
                results.append({
                    "name": "TTS Functionality Test",
                    "accessible": False,
                    "error": str(e)
                })
        
        return {"audio_services_tests": results}
    
    def test_vllm_service(self) -> Dict[str, Any]:
        """Test direct vLLM service."""
        print("\n🧠 Testing vLLM Service")
        print("=" * 50)
        
        results = []
        
        # Test external endpoint
        vllm_result = self.test_endpoint_connectivity(
            self.endpoints["vllm_service"], 
            "External vLLM Service"
        )
        results.append(vllm_result)
        
        # Test single domain endpoint
        vllm_single_result = self.test_endpoint_connectivity(
            f"{self.endpoints['single_domain']}/vllm", 
            "Single Domain vLLM Service"
        )
        results.append(vllm_single_result)
        
        # Test vLLM functionality
        if vllm_result.get("accessible"):
            print("\n🔍 Testing vLLM functionality...")
            try:
                response = requests.post(
                    f"{self.endpoints['vllm_service']}/v1/completions",
                    json={
                        "model": "MiniCPM-V-4",
                        "prompt": "Write a simple Python function:",
                        "max_tokens": 50,
                        "temperature": 0.7
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ vLLM functionality test passed")
                    print(f"   Model: {result.get('model')}")
                    print(f"   Usage: {result.get('usage', {})}")
                    
                    results.append({
                        "name": "vLLM Functionality Test",
                        "accessible": True,
                        "model": result.get('model'),
                        "usage": result.get('usage')
                    })
                else:
                    print(f"   ❌ vLLM functionality test failed: {response.status_code}")
                    results.append({
                        "name": "vLLM Functionality Test",
                        "accessible": False,
                        "error": f"HTTP {response.status_code}"
                    })
            except Exception as e:
                print(f"   ❌ vLLM functionality test error: {e}")
                results.append({
                    "name": "vLLM Functionality Test",
                    "accessible": False,
                    "error": str(e)
                })
        
        return {"vllm_service_tests": results}
    
    def test_dns_resolution(self) -> Dict[str, Any]:
        """Test DNS resolution for all domains."""
        print("\n🌐 Testing DNS Resolution")
        print("=" * 50)
        
        results = []
        domains = [
            f"ai-api.{self.base_domain}",
            f"ai-stt.{self.base_domain}",
            f"ai-tts.{self.base_domain}",
            f"ai-vllm.{self.base_domain}",
            f"ai.{self.base_domain}"
        ]
        
        for domain in domains:
            print(f"🔍 Testing DNS for {domain}")
            try:
                import socket
                ip = socket.gethostbyname(domain)
                print(f"   ✅ {domain} resolves to {ip}")
                results.append({
                    "domain": domain,
                    "resolved": True,
                    "ip": ip
                })
            except socket.gaierror as e:
                print(f"   ❌ {domain} DNS resolution failed: {e}")
                results.append({
                    "domain": domain,
                    "resolved": False,
                    "error": str(e)
                })
        
        return {"dns_tests": results}
    
    def test_ssl_certificates(self) -> Dict[str, Any]:
        """Test SSL certificate validity."""
        print("\n🔒 Testing SSL Certificates")
        print("=" * 50)
        
        results = []
        
        if self.protocol == "https":
            import ssl
            import socket
            from datetime import datetime
            
            domains = [
                f"ai-api.{self.base_domain}",
                f"ai-stt.{self.base_domain}",
                f"ai-tts.{self.base_domain}",
                f"ai-vllm.{self.base_domain}",
                f"ai.{self.base_domain}"
            ]
            
            for domain in domains:
                print(f"🔍 Testing SSL certificate for {domain}")
                try:
                    context = ssl.create_default_context()
                    with socket.create_connection((domain, 443), timeout=10) as sock:
                        with context.wrap_socket(sock, server_hostname=domain) as ssock:
                            cert = ssock.getpeercert()
                            
                            # Check certificate validity
                            not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                            not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                            now = datetime.now()
                            
                            if now < not_after and now > not_before:
                                print(f"   ✅ {domain} has valid SSL certificate")
                                print(f"   Issuer: {cert.get('issuer', {}).get('organizationName', 'Unknown')}")
                                print(f"   Valid until: {cert['notAfter']}")
                                
                                results.append({
                                    "domain": domain,
                                    "valid": True,
                                    "issuer": cert.get('issuer', {}).get('organizationName', 'Unknown'),
                                    "not_after": cert['notAfter'],
                                    "not_before": cert['notBefore']
                                })
                            else:
                                print(f"   ❌ {domain} has invalid SSL certificate")
                                results.append({
                                    "domain": domain,
                                    "valid": False,
                                    "error": "Certificate expired or not yet valid"
                                })
                except Exception as e:
                    print(f"   ❌ {domain} SSL test failed: {e}")
                    results.append({
                        "domain": domain,
                        "valid": False,
                        "error": str(e)
                    })
        else:
            print("   ⚠️ Skipping SSL tests (HTTP mode)")
            results.append({
                "domain": "all",
                "valid": False,
                "error": "HTTP mode - SSL not applicable"
            })
        
        return {"ssl_tests": results}
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all external access tests."""
        print("🧪 EXTERNAL ACCESS TESTING")
        print("=" * 80)
        print(f"Testing external access to AI infrastructure")
        print(f"Base domain: {self.base_domain}")
        print(f"Protocol: {self.protocol}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run all test suites
        test_results = {}
        test_results.update(self.test_dns_resolution())
        test_results.update(self.test_ssl_certificates())
        test_results.update(self.test_routing_api())
        test_results.update(self.test_audio_services())
        test_results.update(self.test_vllm_service())
        
        total_time = time.time() - start_time
        
        # Generate summary
        self.generate_summary_report(test_results, total_time)
        
        return test_results
    
    def generate_summary_report(self, results: Dict[str, Any], total_time: float):
        """Generate a comprehensive summary report."""
        print("\n" + "=" * 80)
        print("📊 EXTERNAL ACCESS TEST SUMMARY")
        print("=" * 80)
        
        total_tests = 0
        successful_tests = 0
        
        for test_suite, tests in results.items():
            if isinstance(tests, list):
                total_tests += len(tests)
                successful_tests += sum(1 for test in tests if test.get('accessible', test.get('resolved', test.get('valid', False))))
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Overall Statistics:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful: {successful_tests}")
        print(f"   Failed: {total_tests - successful_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Total Test Time: {total_time:.2f}s")
        
        print(f"\n📋 Test Suite Breakdown:")
        for test_suite, tests in results.items():
            if isinstance(tests, list):
                suite_total = len(tests)
                suite_success = sum(1 for test in tests if test.get('accessible', test.get('resolved', test.get('valid', False))))
                suite_rate = (suite_success / suite_total * 100) if suite_total > 0 else 0
                print(f"   {test_suite}: {suite_success}/{suite_total} ({suite_rate:.1f}%)")
        
        print(f"\n🌐 External Access URLs:")
        print(f"   Main API:     {self.endpoints['main_api']}")
        print(f"   STT Service:  {self.endpoints['stt_service']}")
        print(f"   TTS Service:  {self.endpoints['tts_service']}")
        print(f"   vLLM Service: {self.endpoints['vllm_service']}")
        print(f"   Single Domain: {self.endpoints['single_domain']}")
        
        print(f"\n🏠 Internal Access URLs:")
        print(f"   Main API:     {self.internal_endpoints['main_api']}")
        print(f"   STT Service:  {self.internal_endpoints['stt_service']}")
        print(f"   TTS Service:  {self.internal_endpoints['tts_service']}")
        print(f"   vLLM Service: {self.internal_endpoints['vllm_service']}")
        
        if success_rate >= 90:
            print(f"\n🎉 EXCELLENT: {success_rate:.1f}% success rate - External access is working perfectly!")
        elif success_rate >= 80:
            print(f"\n✅ GOOD: {success_rate:.1f}% success rate - Minor issues to address")
        else:
            print(f"\n⚠️ NEEDS ATTENTION: {success_rate:.1f}% success rate - Review failed tests")
        
        print("=" * 80)

def main():
    """Main function to run external access testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test external access to AI infrastructure')
    parser.add_argument('--domain', default='yourdomain.com', help='Base domain for testing')
    parser.add_argument('--http', action='store_true', help='Use HTTP instead of HTTPS')
    parser.add_argument('--internal-only', action='store_true', help='Test internal endpoints only')
    
    args = parser.parse_args()
    
    print("🚀 Starting External Access Testing")
    print(f"Domain: {args.domain}")
    print(f"Protocol: {'HTTP' if args.http else 'HTTPS'}")
    
    # Run comprehensive tests
    tester = ExternalAccessTester(
        base_domain=args.domain,
        use_https=not args.http
    )
    
    results = tester.run_comprehensive_test()
    
    # Save results to file
    with open("external_access_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Test results saved to: external_access_test_results.json")
    print(f"🎯 External access testing completed!")

if __name__ == "__main__":
    main()
