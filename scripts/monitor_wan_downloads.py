#!/usr/bin/env python3
"""
Wan Model Download Monitor

This script monitors the download progress of Wan models and sends email notifications
when each model is completed and when all downloads are finished.
"""

import os
import time
import json
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/skadam/gpu-setup/logs/wan_download_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WanDownloadMonitor:
    def __init__(self):
        self.email_api_url = "https://mail.bionicaisolutions.com/api/send"
        self.recipient_email = "salil.kadam@gmail.com"
        self.models_dir = "/opt/ai-models/wan/ti2v-5B"
        self.download_status_file = "/home/skadam/gpu-setup/logs/wan_download_status.json"
        
        # Expected model files and their sizes (in bytes)
        self.expected_files = {
            "Wan2.2_VAE.pth": 2.7 * 1024**3,  # 2.7GB
            "diffusion_pytorch_model-00001-of-00003-bf16.safetensors": 4.58 * 1024**3,  # 4.58GB
            "diffusion_pytorch_model-00002-of-00003-bf16.safetensors": 4.65 * 1024**3,  # 4.65GB
            "diffusion_pytorch_model-00003-of-00003-bf16.safetensors": 86 * 1024**2,  # 86MB
            "models_t5_umt5-xxl-enc-bf16.pth": 10.6 * 1024**3,  # 10.6GB
            "ema.pth": 18.6 * 1024**3,  # 18.6GB
        }
        
        # Load previous status
        self.download_status = self.load_download_status()
        
    def load_download_status(self) -> Dict:
        """Load previous download status from file."""
        if os.path.exists(self.download_status_file):
            try:
                with open(self.download_status_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading download status: {e}")
        return {
            "completed_files": [],
            "last_check": None,
            "total_size_downloaded": 0,
            "total_size_expected": sum(self.expected_files.values()),
            "download_started": datetime.now().isoformat()
        }
    
    def save_download_status(self):
        """Save current download status to file."""
        try:
            os.makedirs(os.path.dirname(self.download_status_file), exist_ok=True)
            with open(self.download_status_file, 'w') as f:
                json.dump(self.download_status, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving download status: {e}")
    
    def get_file_size(self, filepath: str) -> int:
        """Get file size in bytes."""
        try:
            return os.path.getsize(filepath)
        except OSError:
            return 0
    
    def check_download_progress(self) -> Dict:
        """Check current download progress."""
        progress = {
            "timestamp": datetime.now().isoformat(),
            "files": {},
            "total_downloaded": 0,
            "total_expected": self.download_status["total_size_expected"],
            "completion_percentage": 0,
            "newly_completed": []
        }
        
        for filename, expected_size in self.expected_files.items():
            filepath = os.path.join(self.models_dir, filename)
            current_size = self.get_file_size(filepath)
            
            is_complete = current_size >= expected_size * 0.95  # 95% threshold for completion
            
            progress["files"][filename] = {
                "current_size": current_size,
                "expected_size": expected_size,
                "is_complete": is_complete,
                "completion_percentage": (current_size / expected_size * 100) if expected_size > 0 else 0
            }
            
            if is_complete:
                progress["total_downloaded"] += expected_size
                if filename not in self.download_status["completed_files"]:
                    progress["newly_completed"].append(filename)
            else:
                progress["total_downloaded"] += current_size
        
        progress["completion_percentage"] = (progress["total_downloaded"] / progress["total_expected"] * 100)
        
        return progress
    
    def send_email(self, subject: str, body: str, is_html: bool = False):
        """Send email notification using multiple methods."""
        success = False
        
        # Method 1: Try the mail API
        try:
            payload = {
                "to": self.recipient_email,
                "subject": subject,
                "body": body,
                "is_html": is_html
            }
            
            response = requests.post(self.email_api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Email sent successfully via API: {subject}")
                success = True
            else:
                logger.warning(f"API email failed. Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            logger.warning(f"API email error: {e}")
        
        # Method 2: Try SMTP as fallback
        if not success:
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                # SMTP configuration (you may need to adjust these)
                smtp_server = "smtp.gmail.com"
                smtp_port = 587
                smtp_username = "salil.kadam@gmail.com"  # You'll need to use an app password
                smtp_password = os.getenv("GMAIL_APP_PASSWORD", "")  # Set this environment variable
                
                if smtp_password:
                    msg = MIMEMultipart()
                    msg['From'] = smtp_username
                    msg['To'] = self.recipient_email
                    msg['Subject'] = subject
                    
                    if is_html:
                        msg.attach(MIMEText(body, 'html'))
                    else:
                        msg.attach(MIMEText(body, 'plain'))
                    
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    text = msg.as_string()
                    server.sendmail(smtp_username, self.recipient_email, text)
                    server.quit()
                    
                    logger.info(f"Email sent successfully via SMTP: {subject}")
                    success = True
                else:
                    logger.warning("SMTP password not configured. Set GMAIL_APP_PASSWORD environment variable.")
            except Exception as e:
                logger.warning(f"SMTP email error: {e}")
        
        # Method 3: Create a notification file as fallback
        if not success:
            try:
                notification_file = f"/home/skadam/gpu-setup/logs/email_notification_{int(time.time())}.txt"
                with open(notification_file, 'w') as f:
                    f.write(f"Subject: {subject}\n")
                    f.write(f"To: {self.recipient_email}\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"Body:\n{body}\n")
                logger.info(f"Email notification saved to file: {notification_file}")
                success = True
            except Exception as e:
                logger.error(f"Failed to save notification file: {e}")
        
        return success
    
    def format_size(self, size_bytes: int) -> str:
        """Format size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def send_file_completion_notification(self, filename: str, progress: Dict):
        """Send notification when a file is completed."""
        file_info = progress["files"][filename]
        subject = f"Wan Model Download: {filename} Completed"
        
        body = f"""
        <h2>Wan Model Download Progress Update</h2>
        <p><strong>File Completed:</strong> {filename}</p>
        <p><strong>File Size:</strong> {self.format_size(file_info['expected_size'])}</p>
        <p><strong>Overall Progress:</strong> {progress['completion_percentage']:.1f}%</p>
        <p><strong>Total Downloaded:</strong> {self.format_size(progress['total_downloaded'])} / {self.format_size(progress['total_expected'])}</p>
        <p><strong>Timestamp:</strong> {progress['timestamp']}</p>
        
        <h3>Current Status:</h3>
        <ul>
        """
        
        for fname, finfo in progress["files"].items():
            status = "✅ Complete" if finfo["is_complete"] else f"🔄 {finfo['completion_percentage']:.1f}%"
            body += f"<li><strong>{fname}:</strong> {status}</li>"
        
        body += """
        </ul>
        
        <p>Download monitoring will continue until all models are complete.</p>
        """
        
        self.send_email(subject, body, is_html=True)
    
    def send_all_complete_notification(self, progress: Dict):
        """Send notification when all downloads are complete."""
        subject = "Wan Model Download: All Models Completed Successfully! 🎉"
        
        body = f"""
        <h2>🎉 Wan Model Download Complete!</h2>
        <p>All Wan models have been successfully downloaded and are ready for use.</p>
        
        <h3>Download Summary:</h3>
        <ul>
            <li><strong>Total Size:</strong> {self.format_size(progress['total_expected'])}</li>
            <li><strong>Download Time:</strong> {self.calculate_download_time()}</li>
            <li><strong>Completion Time:</strong> {progress['timestamp']}</li>
        </ul>
        
        <h3>Downloaded Models:</h3>
        <ul>
        """
        
        for fname, finfo in progress["files"].items():
            body += f"<li><strong>{fname}:</strong> {self.format_size(finfo['expected_size'])} ✅</li>"
        
        body += """
        </ul>
        
        <h3>Next Steps:</h3>
        <p>The Wan video generation service is now fully operational and ready for production use!</p>
        <ul>
            <li>✅ Service Health: <a href="http://localhost:8004/health">http://localhost:8004/health</a></li>
            <li>✅ Available Models: <a href="http://localhost:8004/models">http://localhost:8004/models</a></li>
            <li>✅ External Access: <a href="https://api.askcollections.com/wan/">https://api.askcollections.com/wan/</a></li>
        </ul>
        
        <p><strong>Wan video generation service is ready for use! 🚀</strong></p>
        """
        
        self.send_email(subject, body, is_html=True)
    
    def calculate_download_time(self) -> str:
        """Calculate total download time."""
        try:
            start_time = datetime.fromisoformat(self.download_status["download_started"])
            end_time = datetime.now()
            duration = end_time - start_time
            
            days = duration.days
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m {seconds}s"
        except:
            return "Unknown"
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle."""
        try:
            logger.info("Starting download progress check...")
            
            # Check if models directory exists
            if not os.path.exists(self.models_dir):
                logger.warning(f"Models directory not found: {self.models_dir}")
                return
            
            # Get current progress
            progress = self.check_download_progress()
            
            # Log progress
            logger.info(f"Download Progress: {progress['completion_percentage']:.1f}% "
                       f"({self.format_size(progress['total_downloaded'])} / {self.format_size(progress['total_expected'])})")
            
            # Check for newly completed files
            for filename in progress["newly_completed"]:
                logger.info(f"File completed: {filename}")
                self.download_status["completed_files"].append(filename)
                self.send_file_completion_notification(filename, progress)
            
            # Check if all downloads are complete
            all_complete = all(finfo["is_complete"] for finfo in progress["files"].values())
            
            if all_complete and len(self.download_status["completed_files"]) == len(self.expected_files):
                logger.info("All downloads completed!")
                self.send_all_complete_notification(progress)
                return True  # Signal to stop monitoring
            
            # Update status
            self.download_status["last_check"] = progress["timestamp"]
            self.download_status["total_size_downloaded"] = progress["total_downloaded"]
            self.save_download_status()
            
            return False  # Continue monitoring
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            return False
    
    def start_monitoring(self, interval_minutes: int = 5):
        """Start continuous monitoring."""
        logger.info(f"Starting Wan download monitoring (checking every {interval_minutes} minutes)")
        logger.info(f"Monitoring directory: {self.models_dir}")
        logger.info(f"Expected files: {list(self.expected_files.keys())}")
        
        # Send initial notification
        initial_subject = "Wan Model Download Monitoring Started"
        initial_body = f"""
        <h2>Wan Model Download Monitoring Started</h2>
        <p>Monitoring has been initiated for Wan model downloads.</p>
        <p><strong>Monitoring Directory:</strong> {self.models_dir}</p>
        <p><strong>Check Interval:</strong> Every {interval_minutes} minutes</p>
        <p><strong>Expected Models:</strong></p>
        <ul>
        """
        
        for filename, size in self.expected_files.items():
            initial_body += f"<li><strong>{filename}:</strong> {self.format_size(size)}</li>"
        
        initial_body += """
        </ul>
        <p>You will receive notifications when each model completes and when all downloads are finished.</p>
        """
        
        self.send_email(initial_subject, initial_body, is_html=True)
        
        # Start monitoring loop
        while True:
            try:
                all_complete = self.run_monitoring_cycle()
                
                if all_complete:
                    logger.info("All downloads completed. Monitoring stopped.")
                    break
                
                logger.info(f"Waiting {interval_minutes} minutes until next check...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user.")
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

def main():
    """Main function."""
    monitor = WanDownloadMonitor()
    monitor.start_monitoring(interval_minutes=5)

if __name__ == "__main__":
    main()
