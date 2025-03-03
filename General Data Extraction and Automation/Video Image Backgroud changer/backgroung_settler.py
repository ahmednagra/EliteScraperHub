import os
import glob
from PIL import Image
import numpy as np
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip


def process_video(video_path, bg_image):
    try:
        # Load the video clip
        video_clip = VideoFileClip(video_path)

        # Get the dimensions of the video
        width, height = video_clip.size

        # Load and resize the background image
        background_image = Image.open(bg_image)
        background_image = background_image.resize((width, height))
        background_image_np = np.array(background_image)
        background_image_clip = ImageClip(background_image_np, duration=video_clip.duration)

        # Composite the video clip and the background image
        final_clip = CompositeVideoClip([background_image_clip, video_clip])

        # Set the output file name and folder
        output_file_name = os.path.splitext(os.path.basename(video_path))[0]
        output_folder = os.path.join("output", output_file_name)
        os.makedirs(output_folder, exist_ok=True)
        output_file_path = os.path.join(output_folder, f"{output_file_name}_processed.mp4")

        # Write the final clip to the output file
        final_clip.write_videofile(output_file_path, codec='libx264', fps=video_clip.fps)

        print(f"Processed: {output_file_path}")
    except Exception as e:
        print(f"Error processing {video_path}: {e}")


if __name__ == "__main__":
    # Paths to input video folders
    video_folders = glob.glob(os.path.join('input', "*"))

    # Process videos in each folder
    for video_folder in video_folders:
        video_files = glob.glob(os.path.join(video_folder, "*.mp4"))
        bg_image = glob.glob(os.path.join(video_folder, "*.jpg"))
        if video_files and bg_image:
            process_video(video_files[0], bg_image[0])
