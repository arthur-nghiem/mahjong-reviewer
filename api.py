"""
api.py: FastAPI wrapper for the Mahjong Reviewer.

Exposes a single POST /review endpoint:
  - Accepts a .jsonl game log and a username
  - Runs the simulator and HTML generator
  - Returns a ZIP of the review (game_review.html + img/)
"""

import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import logging

from config.config import Config
from mahjong_reviewer.simulation import simulator
from mahjong_reviewer.utils import file_util
from dominate import document, tags

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mahjong Reviewer API",
    description="AI-powered Riichi Mahjong game analyzer",
    version="1.0.0",
)

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    """Serve the frontend HTML."""
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    """Health check — used by ECS to confirm the container is ready."""
    return {"status": "ok"}


@app.post("/demo")
async def create_demo_review(background_tasks: BackgroundTasks):
    """
    Generate a demo review using the built-in sample game.
    
    Returns the same ZIP format as /review but uses a pre-loaded game log.
    """
    config = Config()
    
    # Use the sample game from the input directory
    sample_log = Path("input/sample-game.jsonl")
    if not sample_log.exists():
        raise HTTPException(status_code=500, detail="Sample game not found")
    
    # Default username from the sample game
    username = "ampy"
    
    job_id = uuid.uuid4().hex
    work_dir = Path(tempfile.gettempdir()) / f"review_{job_id}"
    work_dir.mkdir(parents=True)

    try:
        # Copy sample log to work dir
        log_path = work_dir / sample_log.name
        log_path.write_bytes(sample_log.read_bytes())
        
        config.LOG_DIR = log_path
        config.REVIEWER_NAME = username
        config.OUTPUT_DIR = work_dir / "output"

        logger.info(f"[{job_id}] Starting DEMO review for {sample_log.name} as {username}")
        
        # Run simulator with config override
        from config.config import Config as ConfigClass
        _original_init = ConfigClass.__init__
        def patched_init(self):
            _original_init(self)
            self.OUTPUT_DIR = config.OUTPUT_DIR
        ConfigClass.__init__ = patched_init
        
        simulator.simulate_game(log_path, username, True)
        
        ConfigClass.__init__ = _original_init
        logger.info(f"[{job_id}] Demo simulator completed")

        # Build HTML review
        game_dir = config.OUTPUT_DIR / log_path.stem
        explanation_path = game_dir / "explanations.jsonl"
        
        if not explanation_path.exists():
            raise HTTPException(status_code=500, detail="Demo review generation failed")

        explanation_list = file_util.read_jsonl_jsonlines(explanation_path)
        doc = document(title="Riichi Mahjong Game Review — Demo")
        with doc.head:
            tags.style("body { font-family: sans-serif; color: #111; max-width: 900px; margin: auto; }")
            tags.meta(charset="utf-8")
        with doc.body:
            tags.h1("Riichi Mahjong Game Review")
            tags.p("Demo review using sample game", style="color: #666; font-style: italic;")
            
            img_dir = game_dir / "img"
            png_files = sorted(img_dir.glob("*.png"))
            
            for idx, filename in enumerate(png_files):
                data = filename.stem.split("-")
                round_counter = f"{data[0][:-1]} {data[0][-1]}"
                repeat_counter = f"Repeat {data[1][-1]}"
                turn_counter = f"Turn {int(data[2][-2:])}"
                agree_symbol = "\U00002705" if data[3] == "True" else "\U0000274c"
                readable = f"{round_counter} {repeat_counter}: {turn_counter} {agree_symbol}"
                with tags.details():
                    tags.summary(readable)
                    tags.img(src=f"img/{filename.name}", alt=readable)
                    if idx < len(explanation_list):
                        tags.p(explanation_list[idx])

        (game_dir / "game_review.html").write_text(doc.render(), encoding="utf-8")

        # Create ZIP
        zip_path = work_dir / f"demo_review.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in game_dir.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(game_dir))
        
        logger.info(f"[{job_id}] Demo review complete: {zip_path.name}")
        
        background_tasks.add_task(shutil.rmtree, work_dir, ignore_errors=True)
        
        return FileResponse(
            path=str(zip_path),
            media_type="application/zip",
            filename="mahjong-demo-review.zip",
        )

    except HTTPException:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise
    except Exception as e:
        logger.error(f"[{job_id}] Demo error: {e}", exc_info=True)
        shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")


@app.post("/review")
async def create_review(
    background_tasks: BackgroundTasks,
    log_file: UploadFile = File(..., description="Game log in .jsonl format"),
    username: str = Form(..., description="Your in-game username"),
):
    """
    Generate a game review from a Mahjong Soul .jsonl log file.

    Returns a ZIP archive containing:
      - game_review.html  (the main review page)
      - img/              (PNG board states referenced by the HTML)
    """
    if not log_file.filename.endswith(".jsonl"):
        raise HTTPException(status_code=400, detail="File must be a .jsonl game log.")

    config = Config()

    # Use a unique temp directory per request so concurrent requests don't collide
    job_id = uuid.uuid4().hex
    work_dir = Path(tempfile.gettempdir()) / f"review_{job_id}"
    work_dir.mkdir(parents=True)

    try:
        # Write uploaded file to temp dir
        log_path = work_dir / log_file.filename
        log_path.write_bytes(await log_file.read())

        # Validate the log contains the username
        events = file_util.read_jsonl_jsonlines(log_path)
        if not events:
            raise HTTPException(status_code=422, detail="Game log is empty.")
        names = events[0].get("names", [])
        if username not in names:
            raise HTTPException(
                status_code=422,
                detail=f"Username '{username}' not found in game log. "
                       f"Players in this log: {', '.join(names)}",
            )

        # Point config at our temp paths
        config.LOG_DIR = log_path
        config.REVIEWER_NAME = username
        config.OUTPUT_DIR = work_dir / "output"

        # Debug logging — check what files/dirs are visible
        import os
        logger.info(f"[{job_id}] Current working directory: {os.getcwd()}")
        logger.info(f"[{job_id}] Files in working dir: {os.listdir('.')}")
        logger.info(f"[{job_id}] Assets directory exists: {os.path.exists('assets')}")
        if os.path.exists('assets'):
            logger.info(f"[{job_id}] Assets contents: {os.listdir('assets')}")
            if os.path.exists('assets/tiles'):
                tile_count = len(os.listdir('assets/tiles'))
                logger.info(f"[{job_id}] Tile images found: {tile_count}")
        logger.info(f"[{job_id}] Config paths: TILES_DIR={config.TILES_DIR}, FONT_DIR={config.FONT_DIR}")

        # Run the simulator — writes PNGs + explanations.jsonl to output/<stem>/
        logger.info(f"[{job_id}] Starting review for {log_file.filename} as {username}")
        logger.info(f"[{job_id}] Config.OUTPUT_DIR set to: {config.OUTPUT_DIR}")
        
        try:
            # CRITICAL: The simulator creates its own Config() internally,
            # so we need to temporarily override the class default
            from config.config import Config as ConfigClass
            original_output_dir = ConfigClass().OUTPUT_DIR
            
            # Monkey-patch: Make Config() return our temp directory
            _original_init = ConfigClass.__init__
            def patched_init(self):
                _original_init(self)
                self.OUTPUT_DIR = config.OUTPUT_DIR
            ConfigClass.__init__ = patched_init
            
            simulator.simulate_game(log_path, username, True)
            
            # Restore original
            ConfigClass.__init__ = _original_init
            
            logger.info(f"[{job_id}] Simulator completed successfully")
            
            # Check what the simulator actually created
            logger.info(f"[{job_id}] Checking what simulator created...")
            logger.info(f"[{job_id}] work_dir contents: {list(work_dir.rglob('*'))[:20]}")
            if config.OUTPUT_DIR.exists():
                logger.info(f"[{job_id}] OUTPUT_DIR contents: {list(config.OUTPUT_DIR.rglob('*'))[:20]}")
        except Exception as sim_error:
            logger.error(
                f"[{job_id}] Simulator failed: {type(sim_error).__name__}: {sim_error}",
                exc_info=True
            )
            raise

        # Build the HTML review
        logger.info(f"[{job_id}] Building HTML review...")
        game_dir = config.OUTPUT_DIR / log_path.stem
        logger.info(f"[{job_id}] Game directory: {game_dir}, exists: {game_dir.exists()}")
        
        if game_dir.exists():
            logger.info(f"[{job_id}] Contents: {list(game_dir.iterdir())}")
        
        explanation_path = game_dir / "explanations.jsonl"
        logger.info(f"[{job_id}] Explanation path: {explanation_path}, exists: {explanation_path.exists()}")
        
        if not explanation_path.exists():
            logger.error(f"[{job_id}] Explanations file not found at {explanation_path}")
            raise HTTPException(status_code=500, detail="Review generation failed.")

        logger.info(f"[{job_id}] Reading explanations...")
        explanation_list = file_util.read_jsonl_jsonlines(explanation_path)
        logger.info(f"[{job_id}] Found {len(explanation_list)} explanations")
        
        logger.info(f"[{job_id}] Building HTML document...")
        doc = document(title="Riichi Mahjong Game Review")
        with doc.head:
            tags.style("body { font-family: sans-serif; color: #111; max-width: 900px; margin: auto; }")
            tags.meta(charset="utf-8")
        with doc.body:
            tags.h1("Riichi Mahjong Game Review")
            
            img_dir = game_dir / "img"
            logger.info(f"[{job_id}] Image directory: {img_dir}, exists: {img_dir.exists()}")
            
            png_files = sorted(img_dir.glob("*.png"))
            logger.info(f"[{job_id}] Found {len(png_files)} PNG files")
            
            for idx, filename in enumerate(png_files):
                data = filename.stem.split("-")
                round_counter = f"{data[0][:-1]} {data[0][-1]}"
                repeat_counter = f"Repeat {data[1][-1]}"
                turn_counter = f"Turn {int(data[2][-2:])}"
                agree_symbol = "\U00002705" if data[3] == "True" else "\U0000274c"
                readable = f"{round_counter} {repeat_counter}: {turn_counter} {agree_symbol}"
                with tags.details():
                    tags.summary(readable)
                    tags.img(src=f"img/{filename.name}", alt=readable)
                    if idx < len(explanation_list):
                        tags.p(explanation_list[idx])

        logger.info(f"[{job_id}] Writing HTML file...")
        (game_dir / "game_review.html").write_text(doc.render(), encoding="utf-8")
        logger.info(f"[{job_id}] HTML file written successfully")

        # Zip the review directory (html + img/)
        logger.info(f"[{job_id}] Creating ZIP archive...")
        zip_path = work_dir / f"review_{log_path.stem}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in game_dir.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(game_dir))
        
        logger.info(f"[{job_id}] ZIP created: {zip_path}, size: {zip_path.stat().st_size} bytes")
        logger.info(f"[{job_id}] Review complete: {zip_path.name}")
        
        # Schedule cleanup AFTER the file is sent
        background_tasks.add_task(shutil.rmtree, work_dir, ignore_errors=True)
        
        return FileResponse(
            path=str(zip_path),
            media_type="application/zip",
            filename=f"review_{log_path.stem}.zip",
        )

    except HTTPException:
        # Clean up on error
        shutil.rmtree(work_dir, ignore_errors=True)
        raise
    except Exception as e:
        logger.error(f"[{job_id}] Unexpected error: {e}", exc_info=True)
        # Clean up on error
        shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")