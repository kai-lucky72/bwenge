#!/usr/bin/env python3
"""
Generate security summary report from various security scan results.
"""

import argparse
import json
import os
import glob
from typing import Dict, List, Any
from pathlib import Path

class SecuritySummaryGenerator:
    """Generates comprehensive security summary from scan results."""
    
    def __init__(self):
        self.summary = {
            "timestamp": "",
            "overall_score": 0,
            "dependency": {"status": "unknown", "issues": 0, "details": []},
            "sast": {"status": "unknown", "issues": 0, "details": []},
            "container": {"status": "unknown", "issues": 0, "details": []},
            "iac": {"status": "unknown", "issues": 0, "details": []},
            "secrets": {"status": "unknown", "issues": 0, "details": []},
            "recommendations": []
        }
    
    def process_dependency_scan(self, scan_dir: str):
        """Process dependency vulnerability scan results."""
        safety_file = os.path.join(scan_dir, "safety-report.json")
        pip_audit_file = os.path.join(scan_dir, "pip-audit-report.json")
        
        total_issues = 0
        details = []
        
        # Process Safety results
        if os.path.exists(safety_file):
            try:
                with open(safety_file, 'r') as f:
                    safety_data = json.load(f)
                
                if isinstance(safety_data, list):
                    for vuln in safety_data:
                        total_issues += 1
                        details.append({
                            "type": "dependency",
                            "severity": vuln.get("vulnerability_id", "unknown"),
                            "package": vuln.get("package_name", "unknown"),
                            "description": vuln.get("advisory", "No description")
                        })
            except Exception as e:
                print(f"Error processing Safety results: {e}")
        
        # Process pip-audit results
        if os.path.exists(pip_audit_file):
            try:
                with open(pip_audit_file, 'r') as f:
                    audit_data = json.load(f)
                
                vulnerabilities = audit_data.get("vulnerabilities", [])
                for vuln in vulnerabilities:
                    total_issues += 1
                    details.append({
                        "type": "dependency",
                        "severity": vuln.get("id", "unknown"),
                        "package": vuln.get("package", {}).get("name", "unknown"),
                        "description": vuln.get("description", "No description")
                    })
            except Exception as e:
                print(f"Error processing pip-audit results: {e}")
        
        self.summary["dependency"] = {
            "status": "pass" if total_issues == 0 else "fail",
            "issues": total_issues,
            "details": details[:10]  # Limit to top 10
        }
    
    def process_sast_scan(self, scan_dir: str):
        """Process SAST scan results."""
        bandit_file = os.path.join(scan_dir, "bandit-report.json")
        semgrep_file = os.path.join(scan_dir, "semgrep-report.json")
        
        total_issues = 0
        details = []
        
        # Process Bandit results
        if os.path.exists(bandit_file):
            try:
                with open(bandit_file, 'r') as f:
                    bandit_data = json.load(f)
                
                results = bandit_data.get("results", [])
                for result in results:
                    if result.get("issue_severity") in ["HIGH", "MEDIUM"]:
                        total_issues += 1
                        details.append({
                            "type": "sast",
                            "severity": result.get("issue_severity", "unknown"),
                            "file": result.get("filename", "unknown"),
                            "description": result.get("issue_text", "No description")
                        })
            except Exception as e:
                print(f"Error processing Bandit results: {e}")
        
        # Process Semgrep results
        if os.path.exists(semgrep_file):
            try:
                with open(semgrep_file, 'r') as f:
                    semgrep_data = json.load(f)
                
                results = semgrep_data.get("results", [])
                for result in results:
                    total_issues += 1
                    details.append({
                        "type": "sast",
                        "severity": result.get("extra", {}).get("severity", "unknown"),
                        "file": result.get("path", "unknown"),
                        "description": result.get("extra", {}).get("message", "No description")
                    })
            except Exception as e:
                print(f"Error processing Semgrep results: {e}")
        
        self.summary["sast"] = {
            "status": "pass" if total_issues == 0 else "fail",
            "issues": total_issues,
            "details": details[:10]
        }
    
    def process_container_scan(self, scan_dir: str):
        """Process container vulnerability scan results."""
        grype_files = glob.glob(os.path.join(scan_dir, "grype-*.json"))
        
        total_issues = 0
        details = []
        
        for grype_file in grype_files:
            try:
                with open(grype_file, 'r') as f:
                    grype_data = json.load(f)
                
                matches = grype_data.get("matches", [])
                for match in matches:
                    vulnerability = match.get("vulnerability", {})
                    severity = vulnerability.get("severity", "unknown")
                    
                    if severity in ["High", "Critical"]:
                        total_issues += 1
                        details.append({
                            "type": "container",
                            "severity": severity,
                            "package": match.get("artifact", {}).get("name", "unknown"),
                            "description": vulnerability.get("description", "No description")
                        })
            except Exception as e:
                print(f"Error processing Grype results from {grype_file}: {e}")
        
        self.summary["container"] = {
            "status": "pass" if total_issues == 0 else "fail",
            "issues": total_issues,
            "details": details[:10]
        }
    
    def process_iac_scan(self, scan_dir: str):
        """Process Infrastructure as Code scan results."""
        terrascan_file = os.path.join(scan_dir, "terrascan-report.json")
        
        total_issues = 0
        details = []
        
        if os.path.exists(terrascan_file):
            try:
                with open(terrascan_file, 'r') as f:
                    terrascan_data = json.load(f)
                
                violations = terrascan_data.get("results", {}).get("violations", [])
                for violation in violations:
                    if violation.get("severity") in ["HIGH", "MEDIUM"]:
                        total_issues += 1
                        details.append({
                            "type": "iac",
                            "severity": violation.get("severity", "unknown"),
                            "file": violation.get("file", "unknown"),
                            "description": violation.get("description", "No description")
                        })
            except Exception as e:
                print(f"Error processing Terrascan results: {e}")
        
        self.summary["iac"] = {
            "status": "pass" if total_issues == 0 else "fail",
            "issues": total_issues,
            "details": details[:10]
        }
    
    def process_secrets_scan(self, scan_dir: str):
        """Process secrets scan results."""
        gitleaks_file = os.path.join(scan_dir, "gitleaks-report.json")
        
        total_issues = 0
        details = []
        
        if os.path.exists(gitleaks_file):
            try:
                with open(gitleaks_file, 'r') as f:
                    gitleaks_data = json.load(f)
                
                if isinstance(gitleaks_data, list):
                    for secret in gitleaks_data:
                        total_issues += 1
                        details.append({
                            "type": "secrets",
                            "severity": "HIGH",
                            "file": secret.get("File", "unknown"),
                            "description": f"Potential secret: {secret.get('RuleID', 'unknown')}"
                        })
            except Exception as e:
                print(f"Error processing GitLeaks results: {e}")
        
        self.summary["secrets"] = {
            "status": "pass" if total_issues == 0 else "fail",
            "issues": total_issues,
            "details": details[:10]
        }
    
    def calculate_overall_score(self):
        """Calculate overall security score."""
        scores = []
        
        # Each category contributes to the score
        categories = ["dependency", "sast", "container", "iac", "secrets"]
        
        for category in categories:
            cat_data = self.summary[category]
            if cat_data["status"] == "pass":
                scores.append(100)
            elif cat_data["status"] == "fail":
                # Score based on number of issues (max penalty of 50 points)
                penalty = min(cat_data["issues"] * 5, 50)
                scores.append(max(0, 100 - penalty))
            else:
                scores.append(50)  # Unknown status
        
        self.summary["overall_score"] = int(sum(scores) / len(scores))
    
    def generate_recommendations(self):
        """Generate security recommendations."""
        recommendations = []
        
        # Check each category for issues
        if self.summary["dependency"]["issues"] > 0:
            recommendations.append("Update vulnerable dependencies to latest secure versions")
        
        if self.summary["sast"]["issues"] > 0:
            recommendations.append("Review and fix static analysis security findings")
        
        if self.summary["container"]["issues"] > 0:
            recommendations.append("Update base images and vulnerable packages in containers")
        
        if self.summary["iac"]["issues"] > 0:
            recommendations.append("Fix Infrastructure as Code security misconfigurations")
        
        if self.summary["secrets"]["issues"] > 0:
            recommendations.append("Remove hardcoded secrets and use secure secret management")
        
        # General recommendations based on score
        if self.summary["overall_score"] < 70:
            recommendations.append("Consider implementing additional security controls")
            recommendations.append("Increase security scanning frequency")
        
        if self.summary["overall_score"] < 50:
            recommendations.append("URGENT: Address critical security issues before deployment")
        
        self.summary["recommendations"] = recommendations
    
    def generate_summary(self, dependency_dir: str = None, sast_dir: str = None,
                        container_dir: str = None, iac_dir: str = None,
                        secrets_dir: str = None) -> Dict[str, Any]:
        """Generate complete security summary."""
        
        import datetime
        self.summary["timestamp"] = datetime.datetime.utcnow().isoformat()
        
        if dependency_dir and os.path.exists(dependency_dir):
            self.process_dependency_scan(dependency_dir)
        
        if sast_dir and os.path.exists(sast_dir):
            self.process_sast_scan(sast_dir)
        
        if container_dir and os.path.exists(container_dir):
            self.process_container_scan(container_dir)
        
        if iac_dir and os.path.exists(iac_dir):
            self.process_iac_scan(iac_dir)
        
        if secrets_dir and os.path.exists(secrets_dir):
            self.process_secrets_scan(secrets_dir)
        
        self.calculate_overall_score()
        self.generate_recommendations()
        
        return self.summary

def main():
    parser = argparse.ArgumentParser(description="Generate security summary report")
    parser.add_argument("--dependency-scan", help="Directory containing dependency scan results")
    parser.add_argument("--sast-scan", help="Directory containing SAST scan results")
    parser.add_argument("--container-scan", help="Directory containing container scan results")
    parser.add_argument("--iac-scan", help="Directory containing IaC scan results")
    parser.add_argument("--secrets-scan", help="Directory containing secrets scan results")
    parser.add_argument("--output", required=True, help="Output file for security summary")
    
    args = parser.parse_args()
    
    generator = SecuritySummaryGenerator()
    
    summary = generator.generate_summary(
        dependency_dir=args.dependency_scan,
        sast_dir=args.sast_scan,
        container_dir=args.container_scan,
        iac_dir=args.iac_scan,
        secrets_dir=args.secrets_scan
    )
    
    # Save summary
    with open(args.output, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print("Security Summary Report")
    print("=" * 50)
    print(f"Overall Security Score: {summary['overall_score']}/100")
    print()
    
    for category in ["dependency", "sast", "container", "iac", "secrets"]:
        cat_data = summary[category]
        status_emoji = "✅" if cat_data["status"] == "pass" else "❌"
        print(f"{status_emoji} {category.title()}: {cat_data['issues']} issues")
    
    if summary["recommendations"]:
        print("\nRecommendations:")
        for rec in summary["recommendations"]:
            print(f"  - {rec}")
    
    print(f"\nDetailed report saved to: {args.output}")

if __name__ == "__main__":
    main()