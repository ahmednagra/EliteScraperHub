import os
import glob
from PIL import Image
import numpy as np
from moviepy.editor import VideoFileClip, clips_array, vfx, ImageClip, CompositeVideoClip


def circle_crop(frame):   # frame rectangle
    height, width, _ = frame.shape
    y, x = np.ogrid[:height, :width]
    center_x, center_y = width // 2, height // 2
    mask = ((x - center_x) ** 2 + (y - center_y) ** 2 > min(center_x, center_y) ** 2)
    # Create a copy of the frame before applying the mask
    cropped_frame = frame.copy()
    cropped_frame[mask] = 0
    return frame

# def circle_crop(frame):  # frame recangle inside round circle fram
#     height, width, _ = frame.shape
#     y, x = np.ogrid[:height, :width]
#     center_x, center_y = width // 2, height // 2
#     mask = ((x - center_x) ** 2 + (y - center_y) ** 2 > min(center_x, center_y) ** 2)
#     cropped_frame = frame.copy()
#     cropped_frame[mask] = 0  # Mask out the frame outside the circle
#     cropped_frame[~mask] = frame[~mask]  # Mask out the frame inside the circle
#     return cropped_frame


def set_background(video_path, image_path):
    try:
        # Extract video file name without extension
        video_name_no_ext = os.path.splitext(os.path.basename(video_path))[0]
        # Create an output folder with the video name if it doesn't exist
        output_folder = os.path.join("output", video_name_no_ext)
        os.makedirs(output_folder, exist_ok=True)
        # Specify the output video file path
        output_video_path = os.path.join(output_folder, f"{video_name_no_ext}_processed.mp4")

        # Load video clip
        video_clip = VideoFileClip(video_path)

        # Get the dimensions of the video
        width, height = video_clip.size

        # Load and resize the background image
        background_image = Image.open(image_path)
        background_image = background_image.resize((width, height))
        background_image_np = np.array(background_image)
        background_image_clip = ImageClip(background_image_np, duration=video_clip.duration)

        # Position the original video clip in the bottom left corner
        # video_positioned = video_clip.resize((int(video_clip.w / 4), int(video_clip.h / 4))).set_position(
        #     ("left", "bottom"))
        video_positioned = video_clip.fl_image(circle_crop).resize((int(width / 4), int(height / 4))).set_position(
            ("left", "bottom"))

        # Combine the background image and the positioned video clip
        # final_clip = clips_array(
        #     [[background_image_clip.set_duration(video_clip.duration),
        #       video_positioned.set_duration(video_clip.duration)]],
        #     bg_color=(255, 255, 255))

        # Composite the video clip and the background image
        final_clip = CompositeVideoClip([background_image_clip, video_positioned])

        # Write the final video to a file
        final_clip.write_videofile(output_video_path, codec='libx264', fps=24)

        # Close the video clips
        video_clip.close()
        background_image.close()

        # Print the output video path and size
        print(f"Output Video Path: {output_video_path}")
        print(f"Output Video Size: {os.path.getsize(output_video_path)} bytes")

    except Exception as e:
        print(f"Error processing video '{video_path}': {e}")


if __name__ == "__main__":
    # Paths to input video folders
    video_folders = glob.glob(os.path.join('input', "*"))

    # Process videos in each folder
    for video_folder in video_folders:
        video_files = glob.glob(os.path.join(video_folder, "*.mp4"))
        bg_image = glob.glob(os.path.join(video_folder, "*.jpg"))
        if video_files and bg_image:
            input_video_path = video_files[0]
            background_image_path = bg_image[0]

            # Call the function to set the background
            print(f"Processing video: {input_video_path}")
            set_background(input_video_path, background_image_path)
        else:
            print(f"No video file or background image found in folder: {video_folder}")
