import subprocess


def join_videos(video1, video2, output_file):
	with open("concat_list.txt", "w") as f:
		f.write(f"file '{video1}'\n")
		f.write(f"file '{video2}'\n")
	
	ffmpeg_cmd = f"ffmpeg -f concat -safe 0 -i concat_list.txt -c copy {output_file}"
	subprocess.run(ffmpeg_cmd, shell=True, check=True)


video1 = "video1.mp4"
video2 = "video2.mp4"
output_file = "joined_video.mp4"

join_videos(video1, video2, output_file)
