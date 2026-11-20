import os
import sys
import time
import logging
from google import genai
from google.genai import types
from typing import Optional

# Set up logger
logger = logging.getLogger(__name__)

GEMINI_API_KEY = None

# Model used for video analysis. Override with GEMINI_MODEL in .env (e.g. gemini-3.1-pro for depth).
GEMINI_MODEL = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"

# Type alias for uploaded files (new google-genai SDK)
File = types.File

def get_gemini_api_key() -> str:
    """
    Get Gemini API key from command line arguments or environment variable.
    Caches the key in memory after first read.
    Priority: command line argument > environment variable

    Returns:
        str: The Gemini API key.

    Raises:
        Exception: If no key is provided in command line arguments or environment.
    """
    global GEMINI_API_KEY
    if GEMINI_API_KEY is None:
        # Try command line argument first
        if "--gemini-api-key" in sys.argv:
            token_index = sys.argv.index("--gemini-api-key") + 1
            if token_index < len(sys.argv):
                GEMINI_API_KEY = sys.argv[token_index]
                logger.info(f"Using Gemini API key from command line arguments")
            else:
                raise Exception("--gemini-api-key argument provided but no key value followed it")
        # Try environment variable
        elif os.getenv("GEMINI_API_KEY"):
            GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
            logger.info(f"Using Gemini API key from environment variable")
        else:
            raise Exception("Gemini API key must be provided via '--gemini-api-key' command line argument or 'GEMINI_API_KEY' environment variable")

    return GEMINI_API_KEY


def configure_gemini() -> genai.Client:
    """
    Configure the Gemini client with the API key.

    Uses the modern google-genai SDK, which supports both the legacy ``AIza``
    keys and the newer ``AQ.`` prefixed keys now issued by Google AI Studio and
    Cloud Console.

    Returns:
        genai.Client: Configured Gemini client for video analysis
    """
    api_key = get_gemini_api_key()
    client = genai.Client(api_key=api_key)

    logger.info("Gemini API configured successfully")
    return client


def upload_video_to_gemini(client: genai.Client, video_path: str) -> File:
    """
    Upload a video file to Gemini File API for analysis.

    Args:
        client: Configured Gemini client
        video_path: Path to the video file to upload

    Returns:
        File: The uploaded file object for use in analysis

    Raises:
        Exception: If upload fails
    """
    try:
        # Upload video file
        video_file = client.files.upload(file=video_path)

        # Wait for processing to complete
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = client.files.get(name=video_file.name)

        if video_file.state.name == "FAILED":
            raise Exception(f"Video processing failed: {video_file.state}")

        logger.info(f"Video uploaded successfully: {video_file.name}")
        return video_file

    except Exception as e:
        logger.error(f"Failed to upload video to Gemini: {str(e)}")
        raise


def analyze_video_with_gemini(client: genai.Client, video_file: File, prompt: str) -> str:
    """
    Analyze a video using Gemini with a custom prompt.

    Args:
        client: Configured Gemini client
        video_file: Uploaded video file from Gemini File API
        prompt: Analysis prompt for the video

    Returns:
        str: Analysis results from Gemini

    Raises:
        Exception: If analysis fails
    """
    try:
        # Generate analysis
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[video_file, prompt],
        )

        if not response.text:
            raise Exception("Gemini returned empty response")

        logger.info("Video analysis completed successfully")
        return response.text

    except Exception as e:
        logger.error(f"Video analysis failed: {str(e)}")
        raise


def cleanup_gemini_file(client: genai.Client, file_name: str):
    """
    Delete a file from Gemini File API to free up storage.

    Args:
        client: Configured Gemini client
        file_name: Name of the file to delete
    """
    try:
        client.files.delete(name=file_name)
        logger.info(f"Cleaned up Gemini file: {file_name}")
    except Exception as e:
        logger.warning(f"Failed to cleanup Gemini file {file_name}: {str(e)}")
