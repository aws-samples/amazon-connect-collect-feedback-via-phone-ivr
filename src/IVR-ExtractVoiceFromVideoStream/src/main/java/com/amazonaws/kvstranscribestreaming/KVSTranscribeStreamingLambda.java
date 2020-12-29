package com.amazonaws.kvstranscribestreaming;

import com.amazonaws.auth.AWSCredentialsProvider;
import com.amazonaws.auth.DefaultAWSCredentialsProviderChain;
import com.amazonaws.kinesisvideo.parser.ebml.InputStreamParserByteSource;
import com.amazonaws.kinesisvideo.parser.ebml.ParserByteSource;
import com.amazonaws.kinesisvideo.parser.mkv.StreamingMkvReader;
import com.amazonaws.kinesisvideo.parser.utilities.FragmentMetadataVisitor;
import com.amazonaws.regions.Regions;
import com.amazonaws.services.cloudwatch.AmazonCloudWatchClientBuilder;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDBClientBuilder;
import com.amazonaws.services.dynamodbv2.document.DynamoDB;
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.SQSEvent;
import com.amazonaws.transcribestreaming.FileByteToAudioEventSubscription;
import com.amazonaws.transcribestreaming.KVSByteToAudioEventSubscription;
import com.amazonaws.transcribestreaming.StreamTranscriptionBehaviorImpl;
import com.amazonaws.transcribestreaming.TranscribeStreamingRetryClient;
import org.reactivestreams.Publisher;
import org.reactivestreams.Subscriber;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import software.amazon.awssdk.auth.credentials.AwsCredentialsProvider;
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.services.transcribestreaming.model.AudioStream;
import software.amazon.awssdk.services.transcribestreaming.model.LanguageCode;
import software.amazon.awssdk.services.transcribestreaming.model.MediaEncoding;
import software.amazon.awssdk.services.transcribestreaming.model.StartStreamTranscriptionRequest;

import java.io.*;
import java.nio.ByteBuffer;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Map;
import java.util.Optional;
import java.util.Date;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/**
 * Demonstrate Amazon Connect's real-time transcription feature using AWS Kinesis Video Streams and AWS Transcribe.
 * The data flow is :
 * <p>
 * Amazon Connect => AWS KVS => AWS Transcribe => AWS DynamoDB
 *
 * <p>Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.</p>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this
 * software and associated documentation files (the "Software"), to deal in the Software
 * without restriction, including without limitation the rights to use, copy, modify,
 * merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so.
 * <p>
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
 * PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */
public class KVSTranscribeStreamingLambda implements RequestHandler<SQSEvent, String> {

    private static final Regions REGION = Regions.fromName(System.getenv("APP_REGION"));
    private static final String RECORDINGS_BUCKET_NAME = System.getenv("RECORDINGS_BUCKET_NAME");

    private static final Logger logger = LoggerFactory.getLogger(KVSTranscribeStreamingLambda.class);
    public static final MetricsUtil metricsUtil = new MetricsUtil(AmazonCloudWatchClientBuilder.defaultClient());
    private static final DateFormat DATE_FORMAT = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSZ");


    // SegmentWriter saves Transcription segments to DynamoDB
    private TranscribedSegmentWriter fromCustomerSegmentWriter = null;
    private TranscribedSegmentWriter toCustomerSegmentWriter = null;

    /**
     * Handler function for the Lambda
     *
     * @param request
     * @param context
     * @return
     */
    @Override
    public String handleRequest(SQSEvent event, Context context) {

        logger.info("received event : " + event.toString());
        logger.info("received context: " + context.toString());

        Map<String, SQSEvent.MessageAttribute> attributes = event.getRecords().get(0).getMessageAttributes();
        String streamARN = attributes.get("StreamARN").getStringValue();
        String startFragmentNum = attributes.get("StartFragmentNumber").getStringValue();
        String contactId = attributes.get("ContactId").getStringValue();

        try {
            logger.info("Start streaming");
            startKVSToTranscribeStreaming(streamARN, startFragmentNum, contactId);
            logger.info("End streaming");
        } catch (Exception e) {
            logger.error("KVS to Transcribe failed with:", e);
        }
        return "{\"Result\": \"Done\"}";
    }

    /**
     * Starts streaming between KVS and Transcribe
     * The transcript segments are continuously saved to the Dynamo DB table
     * At end of the streaming session, the raw audio is saved as an s3 object
     *
     * @param streamARN
     * @param startFragmentNum
     * @param contactId
     * @param languageCode
     * @throws Exception
     */
    private void startKVSToTranscribeStreaming(String streamARN, String startFragmentNum, String contactId) throws Exception {
        String streamName = streamARN.substring(streamARN.indexOf("/") + 1, streamARN.lastIndexOf("/"));
        logger.info("Name of the stream: " + streamName);
        logger.info("Start the stream: " + streamARN);

        Path audioFilePath = Paths.get("/tmp", contactId + ".raw");
        FileOutputStream fileOutputStream = new FileOutputStream(audioFilePath.toString());
        InputStream inputStream = KVSUtils.getInputStreamFromKVS(streamName, REGION, startFragmentNum, getAWSCredentials());
        ParserByteSource parserByteSource = new InputStreamParserByteSource(inputStream);
        StreamingMkvReader streamingMkvReader = StreamingMkvReader.createDefault(parserByteSource);

        FragmentMetadataVisitor.BasicMkvTagProcessor basicTagProcessor = new FragmentMetadataVisitor.BasicMkvTagProcessor();
        FragmentMetadataVisitor fragmentVisitor = FragmentMetadataVisitor.create(Optional.of(basicTagProcessor));

        try {
            logger.info("Start saving audio bytes to location");
            ByteBuffer byteBuffer = KVSUtils.getByteBufferFromStream(streamingMkvReader, fragmentVisitor, basicTagProcessor, contactId);
            while (byteBuffer.remaining() > 0) {
                byte[] audioBytes = new byte[byteBuffer.remaining()];
                byteBuffer.get(audioBytes);
                fileOutputStream.write(audioBytes);
                byteBuffer = KVSUtils.getByteBufferFromStream(streamingMkvReader, fragmentVisitor, basicTagProcessor, contactId);
            }
        } catch (Exception e) {
            logger.error("Error while saving audio bytes", e);
        } finally {
            try {
                inputStream.close();
                fileOutputStream.close();
            } catch (Exception e) {
                logger.error("Error while closing the stream");
            }
            closeFileAndUploadRawAudio(audioFilePath, contactId);
        }
    }

    /**
     * Closes the FileOutputStream and uploads the Raw audio file to S3
     *
     * @param kvsStreamTrackObject
     * @param saveCallRecording should the call recording be uploaded to S3?
     * @throws IOException
     */
    private void closeFileAndUploadRawAudio(Path audioFilePath, String contactId) throws IOException {

        logger.info("Start saving audio file to S3");
        // kvsStreamTrackObject.getInputStream().close();
        // kvsStreamTrackObject.getOutputStream().close();

        File audioFile = new File(audioFilePath.toString());

        if (audioFile.length() > 0) {
            AudioUtils.uploadRawAudio(REGION, RECORDINGS_BUCKET_NAME, "", audioFilePath.toString(), contactId, Boolean.FALSE, getAWSCredentials());
        } else {
            logger.info("No upload to S3. Audio file has no bytes!");
        }

    }

    /**
     * @return AWS credentials to be used to connect to s3 (for fetching and uploading audio) and KVS
     */
    private static AWSCredentialsProvider getAWSCredentials() {
        return DefaultAWSCredentialsProviderChain.getInstance();
    }
}
