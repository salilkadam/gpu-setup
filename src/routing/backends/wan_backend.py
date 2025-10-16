"""
Wan Backend Handler
Handles video generation requests using Wan models
"""

import asyncio
import logging
import requests
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import tempfile
import os

logger = logging.getLogger(__name__)


class WanBackend:
    """Backend handler for Wan video generation models."""
    
    def __init__(self, base_url: str = "http://wan-service:8004"):
        """
        Initialize Wan backend.
        
        Args:
            base_url: Base URL for Wan service
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 300  # 5 minutes timeout for video generation
        
    async def health_check(self) -> bool:
        """Check if Wan service is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Wan service health check failed: {str(e)}")
            return False
    
    async def list_models(self) -> Dict[str, Any]:
        """List available Wan models."""
        try:
            response = self.session.get(f"{self.base_url}/models")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to list Wan models: {str(e)}")
            return {}
    
    async def generate_text_to_video(
        self,
        prompt: str,
        model: str = "t2v-A14B",
        size: str = "1280*720",
        frame_num: Optional[int] = None,
        sample_steps: Optional[int] = None,
        sample_guide_scale: Optional[float] = None,
        base_seed: int = -1,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate video from text prompt."""
        try:
            payload = {
                "task": model,
                "prompt": prompt,
                "size": size,
                "frame_num": frame_num,
                "sample_steps": sample_steps,
                "sample_guide_scale": sample_guide_scale,
                "base_seed": base_seed
            }
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            logger.info(f"Generating text-to-video with model {model}: {prompt[:50]}...")
            
            response = self.session.post(
                f"{self.base_url}/generate/text-to-video",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Text-to-video generation completed: {result.get('success', False)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Text-to-video generation failed: {str(e)}")
            return {
                "success": False,
                "message": f"Generation failed: {str(e)}",
                "error": str(e)
            }
    
    async def generate_image_to_video(
        self,
        prompt: str,
        image_path: str,
        model: str = "i2v-A14B",
        size: str = "1280*720",
        frame_num: Optional[int] = None,
        sample_steps: Optional[int] = None,
        sample_guide_scale: Optional[float] = None,
        base_seed: int = -1,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate video from image and text prompt."""
        try:
            payload = {
                "task": model,
                "prompt": prompt,
                "image_path": image_path,
                "size": size,
                "frame_num": frame_num,
                "sample_steps": sample_steps,
                "sample_guide_scale": sample_guide_scale,
                "base_seed": base_seed
            }
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            logger.info(f"Generating image-to-video with model {model}: {prompt[:50]}...")
            
            response = self.session.post(
                f"{self.base_url}/generate/image-to-video",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Image-to-video generation completed: {result.get('success', False)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Image-to-video generation failed: {str(e)}")
            return {
                "success": False,
                "message": f"Generation failed: {str(e)}",
                "error": str(e)
            }
    
    async def generate_speech_to_video(
        self,
        prompt: str,
        image_path: str,
        audio_path: Optional[str] = None,
        model: str = "s2v-14B",
        enable_tts: bool = False,
        tts_prompt_text: Optional[str] = None,
        tts_text: Optional[str] = None,
        size: str = "1280*720",
        frame_num: Optional[int] = None,
        sample_steps: Optional[int] = None,
        sample_guide_scale: Optional[float] = None,
        base_seed: int = -1,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate video from speech/audio and reference image."""
        try:
            payload = {
                "task": model,
                "prompt": prompt,
                "image_path": image_path,
                "audio_path": audio_path,
                "enable_tts": enable_tts,
                "tts_prompt_text": tts_prompt_text,
                "tts_text": tts_text,
                "size": size,
                "frame_num": frame_num,
                "sample_steps": sample_steps,
                "sample_guide_scale": sample_guide_scale,
                "base_seed": base_seed
            }
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            logger.info(f"Generating speech-to-video with model {model}: {prompt[:50]}...")
            
            response = self.session.post(
                f"{self.base_url}/generate/speech-to-video",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Speech-to-video generation completed: {result.get('success', False)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Speech-to-video generation failed: {str(e)}")
            return {
                "success": False,
                "message": f"Generation failed: {str(e)}",
                "error": str(e)
            }
    
    async def generate_animation(
        self,
        prompt: str,
        src_root_path: str,
        model: str = "animate-14B",
        replace_flag: bool = False,
        refert_num: int = 77,
        size: str = "1280*720",
        frame_num: Optional[int] = None,
        sample_steps: Optional[int] = None,
        sample_guide_scale: Optional[float] = None,
        base_seed: int = -1,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate animation from source path."""
        try:
            payload = {
                "task": model,
                "prompt": prompt,
                "src_root_path": src_root_path,
                "replace_flag": replace_flag,
                "refert_num": refert_num,
                "size": size,
                "frame_num": frame_num,
                "sample_steps": sample_steps,
                "sample_guide_scale": sample_guide_scale,
                "base_seed": base_seed
            }
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            logger.info(f"Generating animation with model {model}: {prompt[:50]}...")
            
            response = self.session.post(
                f"{self.base_url}/generate/animation",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Animation generation completed: {result.get('success', False)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Animation generation failed: {str(e)}")
            return {
                "success": False,
                "message": f"Generation failed: {str(e)}",
                "error": str(e)
            }
    
    async def process_request(
        self,
        model_id: str,
        request_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a video generation request based on model type.
        
        Args:
            model_id: The model identifier (e.g., "t2v-A14B", "i2v-A14B")
            request_data: Request data containing prompt and other parameters
            **kwargs: Additional parameters
            
        Returns:
            Generation result
        """
        try:
            # Determine generation type based on model_id
            if "t2v" in model_id.lower():
                return await self.generate_text_to_video(
                    model=model_id,
                    **request_data,
                    **kwargs
                )
            elif "i2v" in model_id.lower():
                return await self.generate_image_to_video(
                    model=model_id,
                    **request_data,
                    **kwargs
                )
            elif "s2v" in model_id.lower():
                return await self.generate_speech_to_video(
                    model=model_id,
                    **request_data,
                    **kwargs
                )
            elif "animate" in model_id.lower():
                return await self.generate_animation(
                    model=model_id,
                    **request_data,
                    **kwargs
                )
            elif "ti2v" in model_id.lower():
                # TI2V can be treated as I2V for now
                return await self.generate_image_to_video(
                    model=model_id,
                    **request_data,
                    **kwargs
                )
            else:
                # Default to text-to-video
                return await self.generate_text_to_video(
                    model=model_id,
                    **request_data,
                    **kwargs
                )
                
        except Exception as e:
            logger.error(f"Failed to process Wan request: {str(e)}")
            return {
                "success": False,
                "message": f"Request processing failed: {str(e)}",
                "error": str(e)
            }
    
    async def download_video(self, video_filename: str, output_path: str) -> bool:
        """Download generated video."""
        try:
            response = self.session.get(f"{self.base_url}/videos/{video_filename}")
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded video to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download video {video_filename}: {str(e)}")
            return False
    
    async def list_videos(self) -> List[Dict[str, Any]]:
        """List all generated videos."""
        try:
            response = self.session.get(f"{self.base_url}/videos")
            response.raise_for_status()
            
            data = response.json()
            return data.get("videos", [])
            
        except Exception as e:
            logger.error(f"Failed to list videos: {str(e)}")
            return []
    
    async def delete_video(self, video_filename: str) -> bool:
        """Delete a generated video."""
        try:
            response = self.session.delete(f"{self.base_url}/videos/{video_filename}")
            response.raise_for_status()
            
            logger.info(f"Deleted video {video_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete video {video_filename}: {str(e)}")
            return False


# Example usage and testing
if __name__ == "__main__":
    async def test_wan_backend():
        """Test Wan backend functionality."""
        backend = WanBackend()
        
        # Health check
        health = await backend.health_check()
        print(f"Health check: {health}")
        
        if health:
            # List models
            models = await backend.list_models()
            print(f"Available models: {list(models.keys())}")
            
            # Test text-to-video generation
            result = await backend.generate_text_to_video(
                prompt="A beautiful sunset over a calm ocean",
                model="t2v-A14B",
                size="1280*720",
                frame_num=17,
                sample_steps=20,
                sample_guide_scale=7.5,
                base_seed=42
            )
            print(f"Generation result: {result}")
    
    # Run test
    asyncio.run(test_wan_backend())
