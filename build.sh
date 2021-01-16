#!/bin/sh

## Set global variables
ApplicationRegion="YOUR_REGION"  # AllowedPattern: [a-zA-Z0-9-]+
S3SourceBucket="YOUR_S3_BUCKET_WITH_SOURCE_CODE"  # AllowedPattern: [a-zA-Z0-9-]+
S3RecordingsBucketName="THE_S3_BUCKET_SAVING_YOUR_AUDIO_RECORDINGS"  # AllowedPattern: [a-zA-Z0-9-]+
S3TranscriptionBucketName="THE_S3_BUCKET_SAVING_YOUR_TRANSCRIPTIONS"  # AllowedPattern: [a-zA-Z0-9-]+
DynamoDBTableName="YOUR_TABLE_NAME"  # AllowedPattern: [a-zA-Z0-9-]+
SQSQueueName="YOUR_SQS_QUEUE_NAME"  # AllowedPattern: [a-zA-Z0-9]+
CloudFormationStack="YOUR_CLOUD_FORMATION_STACK_NAME"

## Create S3 bucket and set parameters for CloudFormation stack
# Build your paramater string for the CFT
JSON_PARAM="ParameterKey=S3SourceBucket,ParameterValue=%s ParameterKey=DynamoDBTableName,ParameterValue=%s ParameterKey=S3RecordingsBucketName,ParameterValue=%s ParameterKey=S3TranscriptionBucketName,ParameterValue=%s ParameterKey=SQSQueueName,ParameterValue=%s"
JSON_PARAM=$(printf "$JSON_PARAM" "$S3SourceBucket" "$DynamoDBTableName" "$S3RecordingsBucketName" "$S3TranscriptionBucketName" "$SQSQueueName")

# Create your S3 bucket
if [ "$ApplicationRegion" = "us-east-1" ]; then
	aws s3api create-bucket --bucket $S3SourceBucket
else
	aws s3api create-bucket --bucket $S3SourceBucket --create-bucket-configuration LocationConstraint=$ApplicationRegion
fi

## Code build and resource upload
# Build gradle project
echo "Build Gradle Project"
cd src/IVR-ExtractVoiceFromVideoStream/
gradle build
cd ../../

# Create resources
mkdir resources
echo "ZIP Python files"
files="IVR-AddRatings2DynamoDB IVR-Comprehend2DynamoDB IVR-SendStream2SQS IVR-TranscribeWAV2JSON"
for file in $files
do
    output="../../resources/$file.zip"
    cd src/$file
    zip -r $output *.py
    cd ../../
done

echo "Copy Gradle Build to resources"
cp src/IVR-ExtractVoiceFromVideoStream/build/distributions/IVR-ExtractVoiceFromVideoStream.zip resources/IVR-ExtractVoiceFromVideoStream.zip

# Upload resources to S3
echo "Upload files to S3"
aws s3 cp cloudformation/ivr-collect-customer-feedback.json s3://$S3SourceBucket
files="IVR-AddRatings2DynamoDB IVR-Comprehend2DynamoDB IVR-SendStream2SQS IVR-TranscribeWAV2JSON IVR-ExtractVoiceFromVideoStream"
for file in $files
do
    input="resources/$file.zip"
    aws s3 cp $input s3://$S3SourceBucket
done
rm -rf resources

## Run CFT stack creation
aws cloudformation create-stack --stack-name $CloudFormationStack --template-url https://$S3SourceBucket.s3.$ApplicationRegion.amazonaws.com/ivr-collect-customer-feedback.json --parameters $JSON_PARAM --capabilities CAPABILITY_NAMED_IAM
