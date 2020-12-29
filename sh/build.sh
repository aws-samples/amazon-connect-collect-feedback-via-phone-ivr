#!/bin/sh

echo "Build Gradle Project"
cd ../src/IVR-ExtractVoiceFromVideoStream/
gradle build
cd ../../

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

echo "Upload files to S3"
aws s3 cp cloudformation/ivr-collect-customer-feedback.json s3://$1
files="IVR-AddRatings2DynamoDB IVR-Comprehend2DynamoDB IVR-SendStream2SQS IVR-TranscribeWAV2JSON IVR-ExtractVoiceFromVideoStream"
for file in $files
do
    input="resources/$file.zip"
    aws s3 cp $input s3://$1
done
rm -rf resources