import os
import ffmpeg
import boto3
from django.conf import settings
from app.utilities.uploadFileToAws import upload_to_aws
from botocore.exceptions import NoCredentialsError

def compress_video(video_full_path, folder, key, two_pass=True, filename_suffix='_cps' ):
    """
    Compress video file to max-supported size.
    :param video_full_path: the video you want to compress.
    :param size_upper_bound: Max video size in KB.
    :param two_pass: Set to True to enable two-pass calculation.
    :param filename_suffix: Add a suffix for new video.
    :return: out_put_name or error
    """
    s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    filename, extension = os.path.splitext(video_full_path)
    extension = '.mp4'
    output_file_name = filename + filename_suffix + extension

    # Adjust them to meet your minimum requirements (in bps), or maybe this function will refuse your video!

    total_bitrate_lower_bound = 1000000  
    min_audio_bitrate = 128000
    max_audio_bitrate = 320000
    min_video_bitrate = 350000

    try:
        # Bitrate reference: https://en.wikipedia.org/wiki/Bit_rate#Encoding_bit_rate
        probe = ffmpeg.probe(video_full_path)
        # Video duration, in s.
        duration = float(probe['format']['duration'])
        # Audio bitrate, in bps.
        if len(probe['streams'])>1 :
            audio_bitrate = float(next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)['bit_rate'])
        else:
            audio_bitrate = 0    
        videoBitrate = float(next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)['bit_rate'])
        width = probe['streams'][0]['width']
        height = probe['streams'][0]['height']

        # height = (width * 9)/ 16

   
        # read input file and set scale 
        inputFile = ffmpeg.input(video_full_path)
        if width <=720 and height >=1024:
            size_upper_bound = 2000
            ffmpeg.filter(inputFile, 'scale', width='720', height ='1080')
        else:
            size_upper_bound = 10000
            ffmpeg.filter(inputFile, 'scale', width='1080', height ='720')

        # Target total bitrate, in bps.
        target_total_bitrate = (size_upper_bound * 1024 * 8) / (1.073741824 * duration)
        print(audio_bitrate, videoBitrate, height, width)
        
        if target_total_bitrate < total_bitrate_lower_bound:
            print('Bitrate is extremely low! Stop compress!')
            return False

        # Best min size, in kB.
        best_min_size = (min_audio_bitrate + min_video_bitrate) * (1.073741824 * duration) / (8 * 1024)
        print("best_min_size", best_min_size)
        if size_upper_bound < best_min_size:
            print('Quality not good! Recommended minimum size:', '{:,}'.format(int(best_min_size)), 'KB.')
            # return False

        # Target audio bitrate, in bps.
        audio_bitrate = audio_bitrate

        # target audio bitrate, in bps
        if 10 * audio_bitrate > target_total_bitrate:
            audio_bitrate = target_total_bitrate / 10
            if audio_bitrate < min_audio_bitrate < target_total_bitrate:
                audio_bitrate = min_audio_bitrate
            elif audio_bitrate > max_audio_bitrate:
                audio_bitrate = max_audio_bitrate

        # Target video bitrate, in bps.
        video_bitrate = target_total_bitrate - audio_bitrate
        if video_bitrate < 1000:
            print('Bitrate {} is extremely low! Stop compress.'.format(video_bitrate))
            return False

     
        ffmpeg.output(inputFile, output_file_name, 
                        preset="veryfast",
                        **{'c:v': 'libx264', 'b:v': video_bitrate, 'c:a': 'aac', 'b:a': audio_bitrate}
                        ).overwrite_output().run()

        if os.path.getsize(output_file_name) <= size_upper_bound * 1024:
            # success_upload_optimized = upload_to_aws(media, settings.AWS_STORAGE_BUCKET_NAME, folder_name2, file_name2)
            try:
                s3.upload_file(output_file_name, settings.AWS_STORAGE_BUCKET_NAME, folder+key ) 
                print("Upload Successful")
                return True
            except FileNotFoundError:
                print("The file was not found")
                return False
            except NoCredentialsError:
                print("Credentials not available")
                return False
        elif os.path.getsize(output_file_name) < os.path.getsize(video_full_path):  # Do it again
            return compress_video(output_file_name, size_upper_bound)
        else:
            return False
        
    except FileNotFoundError as e:
        print('You do not have ffmpeg installed!', e)
        print('You can install ffmpeg by reading https://github.com/kkroening/ffmpeg-python/issues/251')
        return False