"""
Wan Video Generation Service
Provides API endpoints for text-to-video, image-to-video, speech-to-video, and animation generation
"""

import os
import sys
import logging
import asyncio
import tempfile
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

import torch
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import aiofiles

# Add Wan2.2 to Python path
sys.path.append('/app/Wan2.2')

import wan
from wan.configs import WAN_CONFIGS, SIZE_CONFIGS, MAX_AREA_CONFIGS, SUPPORTED_SIZES
from wan.utils.utils import save_video, merge_video_audio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Wan Video Generation Service",
    description="API for generating videos using Wan models (T2V, I2V, S2V, Animation)",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instances (lazy loaded)
wan_models = {}
model_lock = asyncio.Lock()

# Configuration
MODELS_DIR = os.getenv("MODELS_DIR", "/opt/ai-models")
OUTPUT_DIR = "/app/output"
CACHE_DIR = "/app/cache"

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

class VideoGenerationRequest(BaseModel):
    task: str = Field(..., description="Task type: t2v-A14B, i2v-A14B, ti2v-5B, animate-14B, s2v-14B")
    prompt: str = Field(..., description="Text prompt for video generation")
    size: str = Field(default="1280*720", description="Video size (width*height)")
    frame_num: Optional[int] = Field(default=None, description="Number of frames")
    sample_steps: Optional[int] = Field(default=None, description="Sampling steps")
    sample_guide_scale: Optional[float] = Field(default=None, description="Guidance scale")
    base_seed: int = Field(default=-1, description="Random seed (-1 for random)")
    save_file: Optional[str] = Field(default=None, description="Output filename")

class ImageToVideoRequest(VideoGenerationRequest):
    image_path: str = Field(..., description="Path to input image")

class SpeechToVideoRequest(VideoGenerationRequest):
    image_path: str = Field(..., description="Path to reference image")
    audio_path: Optional[str] = Field(default=None, description="Path to audio file")
    enable_tts: bool = Field(default=False, description="Enable TTS synthesis")
    tts_prompt_audio: Optional[str] = Field(default=None, description="TTS prompt audio path")
    tts_prompt_text: Optional[str] = Field(default=None, description="TTS prompt text")
    tts_text: Optional[str] = Field(default=None, description="Text to synthesize")
    num_clip: Optional[int] = Field(default=None, description="Number of video clips")

class AnimationRequest(VideoGenerationRequest):
    src_root_path: str = Field(..., description="Source root path for animation")
    replace_flag: bool = Field(default=False, description="Use replace mode")
    refert_num: int = Field(default=77, description="Frames for temporal guidance")

class VideoGenerationResponse(BaseModel):
    success: bool
    message: str
    video_path: Optional[str] = None
    task_id: Optional[str] = None
    processing_time: Optional[float] = None

async def get_model(task: str):
    """Get or load the appropriate Wan model for the task"""
    async with model_lock:
        if task not in wan_models:
            logger.info(f"Loading model for task: {task}")
            
            if task not in WAN_CONFIGS:
                raise HTTPException(status_code=400, f"Unsupported task: {task}")
            
            cfg = WAN_CONFIGS[task]
            ckpt_dir = os.path.join(MODELS_DIR, "wan", task)
            
            if not os.path.exists(ckpt_dir):
                raise HTTPException(
                    status_code=404, 
                    f"Model checkpoint not found at {ckpt_dir}. Please download the model first."
                )
            
            try:
                if "t2v" in task:
                    model = wan.WanT2V(
                        config=cfg,
                        checkpoint_dir=ckpt_dir,
                        device_id=0,
                        rank=0,
                        t5_fsdp=False,
                        dit_fsdp=False,
                        use_sp=False,
                        t5_cpu=False,
                        convert_model_dtype=False,
                    )
                elif "ti2v" in task:
                    model = wan.WanTI2V(
                        config=cfg,
                        checkpoint_dir=ckpt_dir,
                        device_id=0,
                        rank=0,
                        t5_fsdp=False,
                        dit_fsdp=False,
                        use_sp=False,
                        t5_cpu=False,
                        convert_model_dtype=False,
                    )
                elif "animate" in task:
                    model = wan.WanAnimate(
                        config=cfg,
                        checkpoint_dir=ckpt_dir,
                        device_id=0,
                        rank=0,
                        t5_fsdp=False,
                        dit_fsdp=False,
                        use_sp=False,
                        t5_cpu=False,
                        convert_model_dtype=False,
                        use_relighting_lora=False
                    )
                elif "s2v" in task:
                    model = wan.WanS2V(
                        config=cfg,
                        checkpoint_dir=ckpt_dir,
                        device_id=0,
                        rank=0,
                        t5_fsdp=False,
                        dit_fsdp=False,
                        use_sp=False,
                        t5_cpu=False,
                        convert_model_dtype=False,
                    )
                else:  # i2v
                    model = wan.WanI2V(
                        config=cfg,
                        checkpoint_dir=ckpt_dir,
                        device_id=0,
                        rank=0,
                        t5_fsdp=False,
                        dit_fsdp=False,
                        use_sp=False,
                        t5_cpu=False,
                        convert_model_dtype=False,
                    )
                
                wan_models[task] = model
                logger.info(f"Model loaded successfully for task: {task}")
                
            except Exception as e:
                logger.error(f"Failed to load model for task {task}: {str(e)}")
                raise HTTPException(status_code=500, f"Failed to load model: {str(e)}")
        
        return wan_models[task]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "wan-video-generation"}

@app.get("/models")
async def list_available_models():
    """List available Wan models and their configurations"""
    available_models = {}
    for task, config in WAN_CONFIGS.items():
        ckpt_dir = os.path.join(MODELS_DIR, "wan", task)
        available_models[task] = {
            "config": {
                "sample_steps": config.sample_steps,
                "sample_guide_scale": config.sample_guide_scale,
                "frame_num": config.frame_num,
                "sample_fps": config.sample_fps
            },
            "available": os.path.exists(ckpt_dir),
            "supported_sizes": SUPPORTED_SIZES.get(task, [])
        }
    return available_models

@app.post("/generate/text-to-video", response_model=VideoGenerationResponse)
async def generate_text_to_video(request: VideoGenerationRequest):
    """Generate video from text prompt"""
    start_time = datetime.now()
    task_id = str(uuid.uuid4())
    
    try:
        # Validate task
        if not request.task.startswith("t2v"):
            raise HTTPException(status_code=400, "Task must be a text-to-video task")
        
        # Get model
        model = await get_model(request.task)
        
        # Generate video
        logger.info(f"Generating video for task {request.task} with prompt: {request.prompt}")
        
        video = model.generate(
            request.prompt,
            size=SIZE_CONFIGS[request.size],
            frame_num=request.frame_num,
            shift=None,
            sample_solver='unipc',
            sampling_steps=request.sample_steps,
            guide_scale=request.sample_guide_scale,
            seed=request.base_seed if request.base_seed >= 0 else None,
            offload_model=True
        )
        
        # Save video
        if request.save_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            request.save_file = f"t2v_{task_id}_{timestamp}.mp4"
        
        output_path = os.path.join(OUTPUT_DIR, request.save_file)
        cfg = WAN_CONFIGS[request.task]
        
        save_video(
            tensor=video[None],
            save_file=output_path,
            fps=cfg.sample_fps,
            nrow=1,
            normalize=True,
            value_range=(-1, 1)
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return VideoGenerationResponse(
            success=True,
            message="Video generated successfully",
            video_path=output_path,
            task_id=task_id,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error generating text-to-video: {str(e)}")
        raise HTTPException(status_code=500, f"Video generation failed: {str(e)}")

@app.post("/generate/image-to-video", response_model=VideoGenerationResponse)
async def generate_image_to_video(request: ImageToVideoRequest):
    """Generate video from image and text prompt"""
    start_time = datetime.now()
    task_id = str(uuid.uuid4())
    
    try:
        # Validate task
        if not request.task.startswith("i2v"):
            raise HTTPException(status_code=400, "Task must be an image-to-video task")
        
        # Check if image exists
        if not os.path.exists(request.image_path):
            raise HTTPException(status_code=404, f"Image not found: {request.image_path}")
        
        # Get model
        model = await get_model(request.task)
        
        # Load image
        from PIL import Image
        img = Image.open(request.image_path).convert("RGB")
        
        # Generate video
        logger.info(f"Generating video for task {request.task} with image: {request.image_path}")
        
        video = model.generate(
            request.prompt,
            img=img,
            max_area=MAX_AREA_CONFIGS[request.size],
            frame_num=request.frame_num,
            shift=None,
            sample_solver='unipc',
            sampling_steps=request.sample_steps,
            guide_scale=request.sample_guide_scale,
            seed=request.base_seed if request.base_seed >= 0 else None,
            offload_model=True
        )
        
        # Save video
        if request.save_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            request.save_file = f"i2v_{task_id}_{timestamp}.mp4"
        
        output_path = os.path.join(OUTPUT_DIR, request.save_file)
        cfg = WAN_CONFIGS[request.task]
        
        save_video(
            tensor=video[None],
            save_file=output_path,
            fps=cfg.sample_fps,
            nrow=1,
            normalize=True,
            value_range=(-1, 1)
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return VideoGenerationResponse(
            success=True,
            message="Video generated successfully",
            video_path=output_path,
            task_id=task_id,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error generating image-to-video: {str(e)}")
        raise HTTPException(status_code=500, f"Video generation failed: {str(e)}")

@app.post("/generate/speech-to-video", response_model=VideoGenerationResponse)
async def generate_speech_to_video(request: SpeechToVideoRequest):
    """Generate video from speech/audio and reference image"""
    start_time = datetime.now()
    task_id = str(uuid.uuid4())
    
    try:
        # Validate task
        if not request.task.startswith("s2v"):
            raise HTTPException(status_code=400, "Task must be a speech-to-video task")
        
        # Check if image exists
        if not os.path.exists(request.image_path):
            raise HTTPException(status_code=404, f"Image not found: {request.image_path}")
        
        # Get model
        model = await get_model(request.task)
        
        # Generate video
        logger.info(f"Generating video for task {request.task} with image: {request.image_path}")
        
        video = model.generate(
            input_prompt=request.prompt,
            ref_image_path=request.image_path,
            audio_path=request.audio_path,
            enable_tts=request.enable_tts,
            tts_prompt_audio=request.tts_prompt_audio,
            tts_prompt_text=request.tts_prompt_text,
            tts_text=request.tts_text,
            num_repeat=request.num_clip,
            pose_video=None,
            max_area=MAX_AREA_CONFIGS[request.size],
            infer_frames=80,
            shift=None,
            sample_solver='unipc',
            sampling_steps=request.sample_steps,
            guide_scale=request.sample_guide_scale,
            seed=request.base_seed if request.base_seed >= 0 else None,
            offload_model=True,
            init_first_frame=False
        )
        
        # Save video
        if request.save_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            request.save_file = f"s2v_{task_id}_{timestamp}.mp4"
        
        output_path = os.path.join(OUTPUT_DIR, request.save_file)
        cfg = WAN_CONFIGS[request.task]
        
        save_video(
            tensor=video[None],
            save_file=output_path,
            fps=cfg.sample_fps,
            nrow=1,
            normalize=True,
            value_range=(-1, 1)
        )
        
        # Merge with audio if provided
        if request.audio_path and os.path.exists(request.audio_path):
            merge_video_audio(video_path=output_path, audio_path=request.audio_path)
        elif request.enable_tts:
            # TTS audio should be saved as tts.wav by the model
            if os.path.exists("tts.wav"):
                merge_video_audio(video_path=output_path, audio_path="tts.wav")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return VideoGenerationResponse(
            success=True,
            message="Video generated successfully",
            video_path=output_path,
            task_id=task_id,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error generating speech-to-video: {str(e)}")
        raise HTTPException(status_code=500, f"Video generation failed: {str(e)}")

@app.post("/generate/animation", response_model=VideoGenerationResponse)
async def generate_animation(request: AnimationRequest):
    """Generate animation from source path"""
    start_time = datetime.now()
    task_id = str(uuid.uuid4())
    
    try:
        # Validate task
        if not request.task.startswith("animate"):
            raise HTTPException(status_code=400, "Task must be an animation task")
        
        # Check if source path exists
        if not os.path.exists(request.src_root_path):
            raise HTTPException(status_code=404, f"Source path not found: {request.src_root_path}")
        
        # Get model
        model = await get_model(request.task)
        
        # Generate video
        logger.info(f"Generating animation for task {request.task} with source: {request.src_root_path}")
        
        video = model.generate(
            src_root_path=request.src_root_path,
            replace_flag=request.replace_flag,
            refert_num=request.refert_num,
            clip_len=request.frame_num,
            shift=None,
            sample_solver='unipc',
            sampling_steps=request.sample_steps,
            guide_scale=request.sample_guide_scale,
            seed=request.base_seed if request.base_seed >= 0 else None,
            offload_model=True
        )
        
        # Save video
        if request.save_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            request.save_file = f"animate_{task_id}_{timestamp}.mp4"
        
        output_path = os.path.join(OUTPUT_DIR, request.save_file)
        cfg = WAN_CONFIGS[request.task]
        
        save_video(
            tensor=video[None],
            save_file=output_path,
            fps=cfg.sample_fps,
            nrow=1,
            normalize=True,
            value_range=(-1, 1)
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return VideoGenerationResponse(
            success=True,
            message="Animation generated successfully",
            video_path=output_path,
            task_id=task_id,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error generating animation: {str(e)}")
        raise HTTPException(status_code=500, f"Animation generation failed: {str(e)}")

@app.get("/videos/{filename}")
async def get_video(filename: str):
    """Download generated video"""
    video_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, "Video not found")
    
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=filename
    )

@app.get("/videos")
async def list_videos():
    """List all generated videos"""
    videos = []
    for filename in os.listdir(OUTPUT_DIR):
        if filename.endswith(('.mp4', '.avi', '.mov')):
            file_path = os.path.join(OUTPUT_DIR, filename)
            stat = os.stat(file_path)
            videos.append({
                "filename": filename,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    
    return {"videos": videos}

@app.delete("/videos/{filename}")
async def delete_video(filename: str):
    """Delete a generated video"""
    video_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, "Video not found")
    
    os.remove(video_path)
    return {"message": f"Video {filename} deleted successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
