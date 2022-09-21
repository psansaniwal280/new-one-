import boto3
from django.conf import settings

def upload_to_aws(file, bucket_location, folder, key):
    
    success = True
    # s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    #Creating Session With Boto3.
    session = boto3.Session(
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

    #Creating S3 Resource From the Session.
    s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    # print(type(file.name))
    
    try:
        print(file)
        # with open(file, "rb") as f:
        #     # fo = io.BytesIO(f)
        s3.upload_fileobj(file, bucket_location, folder+key)
            # s3.Bucket(bucket_location).upload_file(f, folder+key)
        print("Upload Successful")
        return True

    except Exception as err:

        print('An error occurred uploading file to S3: %s' % err)
        return False
